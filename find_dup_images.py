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

todo handle bad user input - e.g. keep index outside range, etc.
todo update the database file when files have been deleted or otherwise changed!!!
todo let user see images after deciding to delete them
todo improve type identification
todo handle any file type?
todo refine the display of multiple alts using matplot lib
todo refine dup handling logic - possibly pull in a menu package, use a cli package, etc.
"""

import argparse
from pathlib import Path
from pprint import pprint as pp
import sys
import time

import yaml

from config import image_extensions
import dupfiles as df

parser = argparse.ArgumentParser()
parser.add_argument('--path', help='Path in which to look for duplicate files, '
                                   'if NOT specified post process saved data from a previous run')
parser.add_argument('--ext-only', action='store_true', help='collect unique file extensions only')
parser.add_argument('--post-process', action='store_true', help='Dispose of duplicates '
                                                                'immediately after finding them')
args = parser.parse_args()

# user wants extensions only
if args.ext_only and args.path:

    exts = df.get_file_extensions(args.path)

    fname = input('Enter filename to save extensions in, enter saves to ./found-exts.yaml: ')

    if fname == '':
        fname = 'found-exts'

    df.save_to_file(exts, fname)

# user wants to find dus and save to file 'dups.out'
elif args.path:

    dups = df.get_duplicates(args.path, image_extensions)

    duration = time.time() - start
    print('Completed looking for duplicate files')
    print(f'found {len(dups)} duplicates in: {time.strftime("%H:%M:%S", time.gmtime(duration))}')

    df.write_dup_list(dups)

    if args.post_process:  # use wanted to process dups immediately after finding them

        df.handle_dup_images(dups)

# assume post processing existing data
else:

    data_file = input('\nEnter fully qualified path to previously generated \n'
                      'data file, or ENTER to use default [./dups.out]: ') or 'dups.out'

    data_file = Path(data_file)  # make the string a pathlib.Path object
    print(f'\nUsing data file {data_file}')

    proceed = input('\n  **** Be sure the source files have not changed since you \n  **** '
                    'ran this script to create the dup data file, continue (y/n/q): ')

    if data_file.is_file() and proceed == 'y':

        with open(data_file, 'r') as f:

            dups = yaml.load(f, Loader=yaml.FullLoader)
            df.handle_dup_images(dups)

    elif data_file.is_file() and proceed in ['', 'n', 'q']:

        sys.exit('\nQuit post processing')

    else:

        print('@@@ ERROR invalid data file')




