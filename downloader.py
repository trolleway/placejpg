#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import subprocess
import logging
import argparse
import sys
import urllib
import pywikibot

from fileprocessor import Fileprocessor
from model_wiki import Model_wiki
modelwiki = Model_wiki()

fileprocessor = Fileprocessor()

parser = argparse.ArgumentParser(
    description="generate IPTC tags for photostock upload by links wikidata "
)

parser.add_argument("filepath", help='url, file or directory with jpg or tiff images')
parser.add_argument("wikidata", type=str, nargs='+', help='ore or many wikidata codes for captions')

parser.add_argument("-с", "--city", type=str, required=True,help='city wikidata object for caption')
parser.add_argument("-dry", "--dry-run", action="store_const",
                    required=False, default=False, const=True)


args = parser.parse_args()

def is_url(url):
    try:
        result = urllib.parse.urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False
        
def get_sdc(pagename,prop):
    site = pywikibot.Site('commons', 'commons')
    file_page = pywikibot.FilePage(site, pagename)
    media_identifier = "M{}".format(file_page.pageid)
    request = site.simple_request(action="wbgetentities", ids=media_identifier)
    raw = request.submit()
    existing_data = raw.get("entities").get(media_identifier)

    try:
        statements = existing_data.get("statements").get(prop)
    except:
        statements = None
    targets=list()
    for statement in statements:
        #print(statement["mainsnak"]["datavalue"]["value"]["id"])
        targets.append(statement["mainsnak"]["datavalue"]["value"]["id"]) 
    return targets


if os.path.isfile(args.filepath):
    files = [args.filepath]
    assert os.path.isfile(args.filepath)
elif os.path.isdir(args.filepath):
    files = os.listdir(args.filepath)
    files = [os.path.join(args.filepath, x) for x in files]
elif is_url(args.filepath):
    pagename = args.filepath
    assert 'File:' in pagename
    
    pagename = pagename.split('File:')[1]
    filename = modelwiki.download_file(pagename,'downloads')

    files = [filename]
else:
    raise Exception("filepath should be file or directory")




city_wdid = fileprocessor.take_user_wikidata_id(
    fileprocessor.prepare_wikidata_url(modelwiki.normalize_wdid(args.city)))
wikidata_ids = list()

for inp_wikidata in args.wikidata:
    piece = fileprocessor.prepare_wikidata_url(modelwiki.normalize_wdid(inp_wikidata))
    wdid = fileprocessor.take_user_wikidata_id(piece)
    
    wikidata_ids.append(wdid)
    

depicts_list = get_sdc(pagename,'P180')
print(depicts_list)
wikidata_ids = wikidata_ids + depicts_list
wikidata_ids = list(set(wikidata_ids))


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
