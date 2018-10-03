from __future__ import print_function

import os.path
import pandas as pd
import json
import argparse

_DATA_DIR = './data'
_TRAIN = 'train.csv'
_TEST = 'test.csv'

_NUM_ROWS_TRAIN = 903653
_NUM_ROWS_TEST = 804684

_NUM_ROWS_DEBUG = 1000


class Dataset():
    """The Google Analytics dataset."""

    def __init__(self, debug=False, skip_rows=False):
        """Load the data from disk.

        Args:
            debug (bool): An option to choose whether to load all
              data.  If 'debug' is true, program will only read 1000 rows
              data from the csv file.
              However, one thing to pay attention is that if you load
              less data, the shape of DF is wrong, because some
              columns daon't have any data until you read many many
              rows.
            skip_rows (bool): An option to load an evenly distributed
              sample of the dataset. If 'debug' is true, _approximately_
              1000 rows will be read from the csv file, but taken every
              _NUM_SKIP_ROWS_TRAIN and _NUM_SKIP_ROWS_TEST rows instead
              of just the first 1000 rows.

        """
        if skip_rows and not debug:
            raise ValueError('debug mode must be on to skip rows')
        rows_to_skip_train = 1
        rows_to_skip_test = 1
        
        if debug and not skip_rows:
            nrows = _NUM_ROWS_DEBUG
        else:
            nrows = None
        if skip_rows:
            rows_to_skip_train = _NUM_ROWS_TRAIN // _NUM_ROWS_DEBUG
            rows_to_skip_test = _NUM_ROWS_TEST // _NUM_ROWS_DEBUG
            
        type_change_columns = {"fullVisitorId": str,
                               "sessionId": str,
                               "visitId": str}
        json_columns = ['device', 'geoNetwork', 'totals', 'trafficSource']

        converters = {column: self.make_json_converter(column)
                      for column in json_columns}

        self.train = pd.read_csv(os.path.join(_DATA_DIR, _TRAIN),
                                 converters=converters,
                                 dtype=type_change_columns,
                                 nrows=nrows, 
                                 skiprows=lambda i: i % rows_to_skip_train !=0)
        self.test = pd.read_csv(os.path.join(_DATA_DIR, _TEST),
                                converters=converters,
                                dtype=type_change_columns,
                                nrows=nrows, 
                                skiprows=lambda i: i % rows_to_skip_test !=0)

        for column in json_columns:
            train_column_as_df = pd.io.json.json_normalize(self.train[column])
            test_column_as_df = pd.io.json.json_normalize(self.test[column])
            self.train = self.train.merge(train_column_as_df,
                                          right_index=True,
                                          left_index=True)
            self.test = self.test.merge(test_column_as_df,
                                        right_index=True,
                                        left_index=True)

    def make_json_converter(self, column_name):
        return lambda x: {column_name: json.loads(x)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Train a model on the Google Analytics Dataset.')
    parser.add_argument('--debug', dest='debug', action='store_true',
                        help='run in debug mode')
    args = parser.parse_args()

    # Make sure we can load the dataset
    dataset = Dataset(debug=args.debug)

    # Sanity check, make sure we have the right number of rows
    num_train = len(dataset.train)
    num_test = len(dataset.test)
    if args.debug:
        assert num_train == _NUM_ROWS_DEBUG
        assert num_test == _NUM_ROWS_DEBUG
    else:
        assert num_train == _NUM_ROWS_TRAIN, 'Incorrect number of training examples found.'
        assert num_test == _NUM_ROWS_TEST, 'Incorrect number of test examples found.'

    print('Successfully loaded the dataset.')
