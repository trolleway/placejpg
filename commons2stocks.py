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


parser.add_argument("-с", "--city", type=str, required=True)
parser.add_argument("-dry", "--dry-run", action="store_const",
                    required=False, default=False, const=True)


args = parser.parse_args()

#open commons file


fileprocessor.commons2stock_dev(args.url, args.city, dry_run = args.dry_run)
quit()

if os.path.isfile(args.filepath):
    files = [args.filepath]
    assert os.path.isfile(args.filepath)
elif os.path.isdir(args.filepath):
    files = os.listdir(args.filepath)
    files = [os.path.join(args.filepath, x) for x in files]
else:
    raise Exception("filepath should be file or directory")



city_wdid = fileprocessor.take_user_wikidata_id(
    fileprocessor.prepare_wikidata_url(args.city))
wikidata_ids = list()
for inp_wikidata in args.wikidata:
    wdid = fileprocessor.take_user_wikidata_id(
        fileprocessor.prepare_wikidata_url(inp_wikidata))
    wikidata_ids.append(wdid)

processed_files = list()
for filename in files:
    if fileprocessor.check_exif_valid(filename):

        caption, keywords = fileprocessor.get_shutterstock_desc(
            filename=filename,
            wikidata_list=wikidata_ids,
            city=city_wdid,

        )

        if args.dry_run:
            print()
            print(filename)
            print(caption)
            print(', '.join(keywords))
            continue

        fileprocessor.write_iptc(filename, caption, keywords)
        processed_files.append(filename)
    else:
        fileprocessor.logger.warning('can not open file '+filename+', skipped')
        continue

if len(processed_files) > 1:
    print('Updated:')
    for element in processed_files:
        print(element)
elif len(processed_files) == 1:
    print('Updated '+processed_files[0])
