#!/usr/bin/env python
"""
poc for finding duplicate files - currently synchronous, eventually
convert to async using asyncio

concept:

    * get a list of file paths
    * compute a hash for each file - store with path (full)
    * check for duplicates

comments:

    * don't need crypto hashes for this I think - ready about xxhash, supposedly good
      for this use case
    * maybe look for dups as they're computed - store the file names w/the hash?

todo rather than delete dups, gather them in a directory for later viewing - this would probably require creating another dup of the "canonical" image
todo handle bad user input - e.g. keep index outside range, etc.
todo duplicate & optimize to use file sizes & hash of first 1k of file before dup detecting (try to cut down on hash time) - will require multiple passes over the list of files
todo improve type identification
todo handle any file type?
todo refine the display of multiple alts using matplot lib
todo refine dup handling logic - possibly pull in a menu package, use a cli package, etc.
"""

import argparse
from pathlib import Path

import yaml

from config import image_extensions
import dupfiles as df

DEFAULT_DATA_FILE_NAME = 'duplicate-images'
FOUND_EXT_LIST_FILE_NAME = 'found-exts'

parser = argparse.ArgumentParser(description='Search for duplicate image files starting in a given directory.  '
                                             'Optionally delete duplicates found or save duplicate data to a '
                                             'file for later processing by this script.\n Typical usage is to '
                                             'find dups first, then delete the files later as finding can take '
                                             'some time.\nThere is also an option to collect extensions, which '
                                             'is intended for testing purposes')
parser.add_argument('--start-path', help='Path in which to begin looking for duplicates')
parser.add_argument('--data-file', help='File to save duplicate data in, or the results of a previous run to process')
parser.add_argument('--find-only', action='store_true', help='Create dup data file only')
parser.add_argument('--exts-only', action='store_true', help=f'collect unique file extensions only, '
                                                             f'written to file {FOUND_EXT_LIST_FILE_NAME}')
args = parser.parse_args()


# primary use case - find only - b/c it can take a long time
if args.start_path is not None and args.find_only and not args.exts_only:

    # dups is a dict keyed on file hash
    dups = df.get_duplicates(args.start_path, image_extensions)

    if args.data_file is None:  # set the default file name
        data_file = Path(DEFAULT_DATA_FILE_NAME)
    else:
        # todo 3 validate the path given
        data_file = Path(args.start_path)

    df.save_to_file(dups, data_file)


# process existing dup data file
elif args.start_path is None and not args.find_only and not args.exts_only:

    if args.data_file is not None:  # user specified data file to use
        data_file = Path(args.data_file)
    else:
        data_file = Path(DEFAULT_DATA_FILE_NAME)

    print(f'@@@ attempting to process {data_file}')

    if data_file.is_file():  # user input validation

        print(f'\nProcessing duplicates using data file: {data_file}')

        # load the data from file
        with open(data_file, 'r') as f:

            dups = yaml.load(f, Loader=yaml.FullLoader)

            deleted_files = df.handle_dup_images(dups)  # capture the files deleted in order to update the db

        df.update_db(deleted_files, dups, data_file)

# find & delete
elif args.start_path is not None and not args.find_only and not args.exts_only:

    # get dup data
    dups = df.get_duplicates(args.start_path, image_extensions)

    # todo move this into get_duplicates()

    if args.data_file is None:  # set the default file name
        data_file = Path(DEFAULT_DATA_FILE_NAME)
    else:
        # todo 3 validate the path given
        data_file = Path(args.start_path)

    deleted_files = df.handle_dup_images(dups)  # user disposes of files, capture the files deleted to update db

    df.update_db(deleted_files, dups, data_file)


# list extensions - mutex w/the previous scenarios
elif args.exts_only and args.start_path is None and args.data_file is None and not args.find_only:

    exts = df.get_file_extensions(args.start_path)

    df.save_to_file(exts, FOUND_EXT_LIST_FILE_NAME)

else:  # invalid argument spec
    print('Invalid option combination specified, please try again')
