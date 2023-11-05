#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import subprocess
import logging
import argparse
import sys
import shutil

from fileprocessor import Fileprocessor
from model_wiki import Model_wiki

fileprocessor = Fileprocessor()
modelwiki = Model_wiki()

parser = argparse.ArgumentParser(
    description="upload photos of object to Wikimedia Commons "
)
parser.add_argument("wikidata", type=str)
parser.add_argument("filepath")
parser.add_argument("-dry", "--dry-run", action="store_const",
                    required=False, default=False, const=True)
parser.add_argument("-l", "--later", action="store_const", required=False,
                    default=False, help='add to job list for upload later', const=True)
parser.add_argument("--verify", action="store_const",
                    required=False, default=False, const=True)
parser.add_argument("--country", type=str, required=False,
                    default='Russia', help='Country for {{Taken on}} template')
parser.add_argument('-s', "--secondary-objects", type=str, nargs='+', required=False,
                    help='secondary wikidata objects, used in category calc with country')
parser.add_argument("--rail", action="store_const", required=False, default=False, const=True,
                    help='add to https://commons.wikimedia.org/wiki/Category:Railway_photographs_by_date')

args = parser.parse_args()

desc_dict = dict()
desc_dict['mode'] = 'object'
desc_dict['wikidata'] = args.wikidata
desc_dict['country'] = args.country
desc_dict['secondary_objects'] = args.secondary_objects
desc_dict['rail'] = args.rail
desc_dict['later'] = args.later
desc_dict['dry_run'] = args.dry_run


fileprocessor.process_and_upload_files(args.filepath, desc_dict)
