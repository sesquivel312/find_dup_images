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
import os
from pathlib import Path
from pprint import pprint as pp
import sys
import time

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from progress.spinner import MoonSpinner
import xxhash
import yaml

from config import image_extensions

parser = argparse.ArgumentParser()
parser.add_argument('--path', help='Path in which to look for duplicate files, '
                                   'if NOT specified post process saved data from a previous run')
parser.add_argument('--ext-only', action='store_true', help='collect unique file extensions only')
parser.add_argument('--post-process', action='store_true', help='Dispose of duplicates '
                                                                'immediately after finding them')
args = parser.parse_args()


def get_file_list(path):
    """
    given directory path, get the full paths of all files in the directory,
    and all subdirectories if the recurse cli arg given, return as a list

    :param path: path to the directory to start in
    :type path: str
    :return: iterator over the file paths
    :rtype: generator
    """

    path = Path(path)   # make a Path object from passed in path value

    files = path.glob('**/*')  # ** means to recurse all subdirs

    return files


def get_file_hash(path, chunk_size=200):
    """
    given the path to a file, read it and return the hash of that file

    :param path: full path to file
    :type path: Path
    :param chunk_size: number of $units of file to read
    :type chunk_size: int
    :return: hexdigest of file hash
    :rtype: str
    """

    with open(path, 'rb') as f:

        xh = xxhash.xxh64(f.read(chunk_size))

        while True:

            chunk = f.read(chunk_size)

            if not chunk:
                break

            xh.update(chunk)

        return xh.hexdigest()


def build_file_db(start_dir, extensions):
    """
    return a database containing info for each file under the
    starting path/directory

    :param extensions:
    :param start_dir: directory in which to start
    :type start_dir: str
    :return: a 2-tuple containing the info db and time to run this function
    :rtype: tuple
    """

    if not extensions:
        sys.exit('@@@ERROR valid extension list not passed to build_file_db')

    db = {}

    spinner = MoonSpinner('Working ')  # cli spinner to indicate something is happening

    for p in get_file_list(start_dir):

        # got a file (not a dir) and filename has relevant extension
        if p.is_file() and p.suffix.lower() in extensions:

            pstring = str(p)

            xh = get_file_hash(p)

            # first time seeing this file
            if xh not in db:

                db[xh] = [{'path': pstring, 'extension': p.suffix.lower(), }]

            # found another alt for xh, add it to the alts key
            else:

                db[xh].append({'path': pstring, 'extension': p.suffix.lower(), })

        spinner.next()

    print('\n')

    return db


def get_file_extensions(start_dir):
    """
    return a database containing the unique file extensions of files in a given directory
    starting path/directory

    todo track count of each extension type

    :param start_dir: directory in which to start
    :type start_dir: str
    :return: a 2-tuple containing the info db and time to run this function
    :rtype: tuple
    """

    exts = set()

    spinner = MoonSpinner('Working ')  # cli spinner to indicate something is happening

    for p in get_file_list(start_dir):

        if p.is_file():

            exts.add(p.suffix.lower())

        spinner.next()

    print('\n')

    return exts


def get_duplicates(start_path, extensions):
    """
    get the duplicates from a file info db created by build_file_db

    :param extensions:
    :param file_info_db: dict returned by build_file_db
    :type file_info_db: dict
    :return: dict of dup files only
    :rtype: tbd
    """

    if not extensions:
        sys.exit('@@@ERROR - invalid extension list in get_duplicates')

    file_info_db = build_file_db(start_path, extensions)

    dup_free_db = {}

    for hash, alts in file_info_db.items():

        if not len(alts) == 1:  # has a dup, record that fact

            # make the first path the "canonical" path, then add the list of alts -
            # except for the first one
            dup_free_db[file_info_db[hash][0]['path']] = alts[1:]

    return dup_free_db


def show_images_mp(images):
    """
    display bitmap images from a list

    :param images: list of fully qualified file names
    :type images: list
    :return: Nothing
    :rtype: None
    """

    n = len(images)  # we'll need the number of alts a couple times

    fig, axs = plt.subplots(n, 1)  # 1 x n array of charts (pyplot axes)

    for i, image in enumerate(images):

        img = mpimg.imread(image)  # put the pixel data into a pyplot plottable array/form
        axs[i].set_title(str(image))
        axs[i].imshow(img)  # put the image data onto the current axes

    plt.show()


def get_alt_file_names(alt_data):
    """
    given a list of alternate file data (dicts) return a list of only the alt file names

    Notes:
        alt_list is of the form:
        [{'extension': $ext, 'mime_type': $mt, 'path': $path}, ...]

    :param alt_data: data about the duplicates of a single, "canonical" file
    :type alt_data: list
    :return: list of all alternative file names
    :rtype: list
    """

    alt_file_list = []

    for alt in alt_data:

        alt_file_list.append(alt['path'])

    return alt_file_list


def handle_dup_images(duplicates):
    """
    given a data structure containing dup image file info, let user choose an action to take
    on each alternative set of images, i.e. so a human may confirm they are in fact duplicates,
    etc.

    Notes:
        The duplicates data structure is:
        {
          $pathlib.Path: [
            'extension': $file_ext,
            'mime_type': $mime_type,
            'path': $pathlib.Path
           ]
        }

    :param duplicates: data structure containing duplicate image file info
    :return:
    """

    for file, data in duplicates.items():

        alts = get_alt_file_names(data)

        alts.insert(0, file)  # put the "canonical" file name first - which was the key to this dup dict entry

        print(f'\nWhat would you like to do with dups of: {alts[0]}?\n')

        action = input('  (s)how alts, (d)elete alts, futures_here, ENTER to skip & continue: ')

        if action is not None:
            if action == 's':
                show_images_mp(alts)
                action = input('  Delete alts for this set (y/n)?: ')
                if action == 'y':
                    delete_alts(alts)
            if action == 'd':
                delete_alts(alts)
        else:
            continue


def delete_alts(alts):
    """
    delete the redundant images in a list

    :param alts: alternative image file name/path - including the "canonical" image file
    :type alts: list
    :return: TBD
    :rtype: TBD
    """

    print('  The list of duplicates is...\n')

    for i, alt in enumerate(alts):

        print(f'  {i}: {alt}')

    img_to_delete = input('\nWhich one to *KEEP* (enter number): ')
    img_to_delete = int(img_to_delete)  # will be str, need int

    if img_to_delete is not None:

        really = input(f'Really delete duplicates of {alts[img_to_delete]}?  Enter "yes": ')

        if really is not None and really == 'yes':  # really want to delete OTHER images

            alts.pop(img_to_delete)  # remove the keeper from the alt list

            for alt in alts:
                os.remove(alt)

        else:

            print('Skipping... MUST enter "yes", not just "y"')


def write_dup_list(dups):
    """
    write the duplicate file "list" to a file

    :param dups: duplicates
    :type dups: dict
    :return: Nothing
    :rtype: None
    """

    with open('dups.out', 'w') as f:

        yaml.dump(dups, f)


if __name__ == '__main__':

    start = time.time()

    # user wants extensions only
    if args.ext_only and args.path:

        exts = get_file_extensions(args.path)

        duration = time.time() - start
        print('Completed looking for unique file extensions')
        print(f'found {len(exts)} extensions in: {time.strftime("%H:%M:%S", time.gmtime(duration))}')
        pp(exts)

    # user wants to find dus and save to file 'dups.out'
    elif args.path:

        dups = get_duplicates(args.path, image_extensions)

        duration = time.time() - start
        print('Completed looking for duplicate files')
        print(f'found {len(dups)} duplicates in: {time.strftime("%H:%M:%S", time.gmtime(duration))}')

        write_dup_list(dups)

        if args.post_process:  # use wanted to process dups immediately after finding them

            handle_dup_images(dups)

    # assume post processing existing data
    else:

        data_file = input('Enter fully qualified path to previously generated '
                          'data file, or ENTER to use default: ') or 'dups.out'

        data_file = Path(data_file)  # make the string a pathlib.Path object

        proceed = input('\n\n**** BE SURE THE SOURCE FILES HAVE NOT CHANGED\nSINCE YOU RAN THIS '
                        'SCRIPT TO CREATE THE DUP DATA FILE, continue (y/n): ')

        if data_file.is_file() and proceed == 'y':

            with open(data_file, 'r') as f:

                dups = yaml.load(f, Loader=yaml.FullLoader)
                handle_dup_images(dups)

        elif data_file.is_file() and (proceed == '' or proceed == 'n'):

            print('*** Exiting ***')

        else:

            print('@@@ ERROR invalid data file')




