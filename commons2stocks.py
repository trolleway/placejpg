#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import subprocess
import logging
import argparse
import sys


from fileprocessor import Fileprocessor

fileprocessor = Fileprocessor()

parser = argparse.ArgumentParser(
    description="Download photo from Commons, read wikidata objects, generate IPTC tags for photostock upload "
)

parser.add_argument("url",help='URL of Wikimedia commons file')


parser.add_argument("-с", "--city", type=str, required=True, help='City object, wikidata id or wikidata name')
parser.add_argument("-dry", "--dry-run", action="store_const",
                    required=False, default=False, const=True)
parser.add_argument("--date", type=str, required=False, help='use YYYY-MM-DD date if can not read from EXIF')


args = parser.parse_args()

#open commons file


fileprocessor.commons2stock_dev(args.url, args.city, dry_run = args.dry_run, date=args.date)
