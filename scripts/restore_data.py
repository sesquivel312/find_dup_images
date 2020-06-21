"""
a directory w/test files exists in the project, actually two.  One that is the "backup" or
default state, and another that the dup remover is run against.  They are used like so:

copy data-default to data
run tool against data
if files in data changed, delete data, then
copy data-default to data

This script automates that

It assumes the directory is one directory above the one this script is run from
"""

import os
from pathlib import Path
import shutil

RESET = Path('c:\\Users\\steve\\dev\\scratch\\find_dups\\data-reset')
WORKING = Path('c:\\Users\\steve\\dev\\scratch\\find_dups\\data')
DUP_DB_FILE = Path('c:\\Users\\steve\\dev\\scratch\\find_dups\\duplicate-images')

if WORKING.exists():
    shutil.rmtree(WORKING)
if DUP_DB_FILE.exists():
    os.remove(DUP_DB_FILE)
shutil.copytree(RESET, WORKING)



