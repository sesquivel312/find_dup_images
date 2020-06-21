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

todo update the database file when files have been deleted or otherwise changed!!!
todo handle bad user input - e.g. keep index outside range, etc. @@ allow user at least two tries to delete when view during delete
todo improve the way user input is handled - factor out of functions, loops?
todo improve type identification
todo handle any file type?
todo refine the display of multiple alts using matplot lib
todo refine dup handling logic - possibly pull in a menu package, use a cli package, etc.
"""

import os
from pathlib import Path
import sys
import time

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from progress.spinner import MoonSpinner
import xxhash
import yaml

from config import image_extensions


def save_to_file(data, fname=None):
    """
    save a data structure to a yaml file

    :param fname: name of file to save
    :param data: data - a list, tuple, dict, etc.
    :type data: multiple
    :return: TBD
    """

    if fname is None:
        sys.exit('@@@ Attempted to save a file without providing a name, existing...')

    fname = Path(fname)

    with open(fname, 'w') as f:
        yaml.dump(data, f)


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

    for p in get_file_list(start_dir):   # loop over all the Paths (files) in the hierarchy starting at start_dir

        # got a file (not a dir) and filename has an extension of interest
        if p.is_file() and p.suffix.lower() in extensions:

            pstring = str(p)  # get the Path in string form

            xh = get_file_hash(p)

            # first time seeing this file
            if xh not in db:

                db[xh] = [{'path': pstring, 'extension': p.suffix.lower(), }]

            # found a likely alt of an existing file, add it to the alts key for for the existing file
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

    start = time.time()

    for p in get_file_list(start_dir):

        if p.is_file():

            exts.add(p.suffix.lower())

        spinner.next()

    duration = time.time() - start

    print('\n')

    print('Completed looking for unique file extensions')
    print(f'found {len(exts)} extensions in: {time.strftime("%H:%M:%S", time.gmtime(duration))}')
    print(f'Extensions found: {exts}')

    return exts


def get_duplicates(start_path, extensions):
    """
    get the duplicates from a file info db created by build_file_db

    :param start_path: file system path in which to start looking for duplicates
    :type start_path: pathlib.Path
    :param extensions: collection of file extensions that identify files of interest
    :return: dict of dup files only
    :rtype: tbd
    """

    if not extensions:
        sys.exit('@@@ERROR - invalid extension list in get_duplicates')

    file_info_db = build_file_db(start_path, extensions)  # get file hashes and dup info

    dup_free_db = {}

    start = time.time()

    for hash, alts in file_info_db.items():

        if not len(alts) == 1:  # has a dup, record that fact

            # make the first path the "canonical" path, then add the list of alts -
            # except for the first one
            dup_free_db[file_info_db[hash][0]['path']] = alts[1:]

    print(f'found {len(dup_free_db)} duplicates in: {time.time() - start}')

    return dup_free_db


def show_images(images):
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

    # records the names of files that are deleted, used to remove from the dup DB before resaving it
    deleted_file_list = []

    for fname, data in duplicates.items():

        alts = get_alt_file_names(data)

        alts.insert(0, fname)  # put the "canonical" file name first - which was the key to this dup dict entry

        print(f'\n@@@ Now processing: {alts[0]}\nWhat would you like to do with duplicates of this image?\n')

        action = input('  (s)how alts, (d)elete alts, (q)uit, futures_here, ENTER to skip & continue: ')

        if action in ['s', 'S']:

            show_images(alts)

            action = input('  Delete alts for this set (y/n)?: ')

            if action in ['y', 'Y']:

                delete_alts(alts)

                deleted_file_list.append(fname)  # remove the entry from the dup db todo add exception handling (KeyError?)

        if action in ['d', 'D']:

            delete_alts(alts)

            deleted_file_list.append(fname)  # same as previous instance of this line

    return deleted_file_list


def get_numeric_user_input(min, max, prompt):
    """
    get user input - expecting an positive integer between min and max - inclusive

    Prompt user using the prompt string provided

    :param prompt:
    :param range:
    :return:
    """

    # todo verify params are integers and max > min

    while True:

        value = input(prompt)

        try:
            value = int(value)
        except ValueError:
            continue

        # we got a number, check for range

        if min <= value <= max:

            return value


def delete_alts(alts):
    """
    delete the redundant images in a list

    :param alts: alternative image file name/path - including the "canonical" image file
    :type alts: list
    :return: code indicating success (0) or failure (anything else)
    :rtype: int
    """

    # print list of alts with numbers to select a keeper
    print('  The list of duplicates is...\n')
    for i, alt in enumerate(alts):
        print(f'  {i}: {alt}')

    selection = input('\nWhich one to *KEEP* (enter number), or "v" to view images: ')

    # display the images
    if selection in ['v', 'V']:
        show_images(alts)

        # reprompt for alt to delete (assuming can still see the
        # previously displayed list
        selection = input('\nWhich one to *KEEP* (enter number): ')

    try:
        selection = int(selection)
    except ValueError as e:
        selection = input(f'Please enter a number from the the list shown above: ')

    # validate user input
    if selection not in range(len(alts)):  # entered a number outside possible values

        selection = input('Your selection was out of range, please enter '
                          'the number of one of the displayed alts: ')
        try:
            selection = int(selection)
        except ValueError as e:
            print(f'Still not a number, skipping this one...')
            return -1

        if selection not in range(len(alts)):  # second time user entered a number out of range
            print('Selection is not one of the displayed options, skipping...')
            return -1

    really = input(f'Really delete duplicates of {alts[selection]}, enter "y": ')

    if really in ['y', 'Y']:  # really want to delete OTHER images

        alts.pop(selection)  # remove the keeper from the alt list - i.e. "keep it"

        for alt in alts:
            os.remove(alt)

    else:

        print('Skipping... must enter "y" to delete')


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


def check_for_collisions(hashes):
    """
    todo write this function that ...

    Given a list of hashes, checks for duplicates

    ideas:

        I think the collections library has a way to produce dict counts by key
        ??? actually is this even possible - I add dups when the hash is the same,
        So I expect dups - what I want to avoid is different files w/the same hash
        need other info on that - perhaps check file name, image info such as location
        and date, etc.

    :param hashes:
    :return:
    """

    pass


def update_db(deleted_files, duplicate_db, db_file_name):
    """
    remove the entries from the duplicate file db whose files have been removed from
    the filesystem by the user

    given the dup DB (dict) and an entry, delete said entry

    Would use this when the file was deleted at users request

    :param db_file_name: name of the file to save the updated db to
    :type db_file_name: pathlib.Path
    :param deleted_files: list of files to be removed from the db
    :type deleted_files: list
    :param duplicate_db: dict of duplicate files, keyed on fully qualified file name of "canonical" alternate
    :type duplicate_db: dict
    :return: None
    """

    # todo validate db_file_name

    for f in deleted_files:

        duplicate_db.pop(f)

    with open(db_file_name, 'w') as f:  # open for write, will truncate the file first

        yaml.dump(duplicate_db, f)







