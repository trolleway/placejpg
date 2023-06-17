#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os, subprocess, logging, argparse, sys

from fileprocessor import Fileprocessor
from model_wiki import Model_wiki

fileprocessor = Fileprocessor()
modelwiki = Model_wiki()

parser = argparse.ArgumentParser(
    description="upload photos of buildings to Wikimedia Commons "
)
parser.add_argument("wikidata", type=str)
parser.add_argument("filepath")
parser.add_argument(
    "-dry", "--dry-run", action="store_const", required=False, default=False, const=True
)
parser.add_argument(
    "--verify", action="store_const", required=False, default=False, const=True
)
parser.add_argument("--country", type=str,required=False, default='Russia', help='Country for {{Taken on}} template')
parser.add_argument('-s',"--secondary-objects", type=str, nargs='+',required=False,  help='secondary wikidata objects, used in category calc with country')
parser.add_argument("--rail", action="store_const", required=False, default=False, const=True, help='add to https://commons.wikimedia.org/wiki/Category:Railway_photographs_by_date')
parser.add_argument(
    "--no-building",
    action="store_const",
    required=False,
    default=False,
    const=True,
    help="Upload files for any Wikidata object witch has name en, name ru and commons category",
)
args = parser.parse_args()

if os.path.isfile(args.filepath):
    files = [args.filepath]
    assert os.path.isfile(args.filepath)
elif os.path.isdir(args.filepath):
    files = os.listdir(args.filepath)
    files = [os.path.join(args.filepath, x) for x in files]
else:
    raise Exception("filepath should be file or directory")



#wikidata = fileprocessor.take_user_wikidata_id(fileprocessor.prepare_wikidata_url(args.wikidata))
from model_wiki import Model_wiki
modelwiki = Model_wiki()
wikidata = modelwiki.wikidata_input2id(args.wikidata)
secondary_wikidata_ids = modelwiki.input2list_wikidata(args.secondary_objects)


uploaded_paths = list()
for filename in files:
    if fileprocessor.check_exif_valid(filename):
        print(filename+' valid')
        if args.no_building:
            texts = fileprocessor.make_image_texts_simple(
                filename=filename,
                wikidata=wikidata,
                country=args.country.capitalize(),
                rail=args.rail,
                secondary_wikidata_ids = secondary_wikidata_ids
            )            
        else:
            
            texts = fileprocessor.make_image_texts_building(
                filename=filename,
                wikidata=wikidata,
                place_en="Moscow",
                place_ru="Москва",
                no_building=args.no_building,
                country=args.country.capitalize(),
                rail=args.rail
            )

        if args.dry_run:
            print()
            print(texts["name"])
            print(texts["text"])


        wikidata_list = list()
        wikidata_list.append(wikidata)
        wikidata_list += secondary_wikidata_ids
        
        if not args.dry_run:
            fileprocessor.upload_file(
                filename, texts["name"], texts["text"], verify_description=args.verify
            )
        modelwiki.append_image_descripts_claim(texts["name"], wikidata_list, args.dry_run)
        if not args.dry_run:
            modelwiki.create_category_taken_on_day(args.country.capitalize(),texts['dt_obj'].strftime("%Y-%m-%d"))
        else:
            print('will append '+' '.join(wikidata_list))
            
        uploaded_paths.append('https://commons.wikimedia.org/wiki/File:'+texts["name"].replace(' ', '_'))
    else:
        print('can not open file '+filename+', skipped')
        continue

if not args.dry_run:
    print('uploaded: ')
else:
    print('emulating upload. URL will be: ')

print("\n".join(uploaded_paths))
        
