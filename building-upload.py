#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os, subprocess, logging, argparse, sys, shutil

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
parser.add_argument("--location", type=str,required=False, default='Russia', help='Country for {{Taken on}} template')
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

files, uploaded_folder_path = fileprocessor.input2filelist(args.filepath)

if len(files)==0:
    print('all files already uploaded')
    quit()
'''
if os.path.isfile(args.filepath):
    files = [args.filepath]
    assert os.path.isfile(args.filepath)
    uploaded_folder_path = os.path.join(os.path.dirname(args.filepath),'commons_uploaded')
elif os.path.isdir(args.filepath):
    files = os.listdir(args.filepath)
    files = [os.path.join(args.filepath, x) for x in files]
    uploaded_folder_path = os.path.join(args.filepath,'commons_uploaded')
else:
    raise Exception("filepath should be file or directory")
'''


#wikidata = fileprocessor.take_user_wikidata_id(fileprocessor.prepare_wikidata_url(args.wikidata))
from model_wiki import Model_wiki
modelwiki = Model_wiki()
wikidata = modelwiki.wikidata_input2id(args.wikidata)
secondary_wikidata_ids = modelwiki.input2list_wikidata(args.secondary_objects)


uploaded_paths = list()
for filename in files:
    if 'commons_uploaded' in filename: continue
    if fileprocessor.check_exif_valid(filename):
        if args.no_building:
            texts = fileprocessor.make_image_texts_simple(
                filename=filename,
                wikidata=wikidata,
                country=args.location.capitalize(),
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
                country=args.location.capitalize(),
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
            modelwiki.create_category_taken_on_day(args.location.capitalize(),texts['dt_obj'].strftime("%Y-%m-%d"))
        else:
            print('will append '+' '.join(wikidata_list))
            
        uploaded_paths.append('https://commons.wikimedia.org/wiki/File:'+texts["name"].replace(' ', '_'))
        
        if not args.dry_run:
            if not os.path.exists(uploaded_folder_path):
                os.makedirs(uploaded_folder_path)
            shutil.move(filename, os.path.join(uploaded_folder_path, os.path.basename(filename)))
   
    else:
        print('can not open file '+filename+', skipped')
        continue

if not args.dry_run:
    print('uploaded: ')
else:
    print('emulating upload. URL will be: ')

print("\n".join(uploaded_paths))

if args.dry_run:
    add_queue = input("Add to queue? Y/N    ")

    if add_queue.upper()=='Y':
        cmd = 'python3 building-upload.py '
        if args.no_building: cmd += '--no-building '
        cmd += wikidata + ' '
        cmd += '"'+args.filepath + '" '
        if args.location: cmd += '--location "'+ args.location + '" '
        if len(secondary_wikidata_ids)>0: cmd += '-s ' + ' '.join(secondary_wikidata_ids)
        
        print('adding to queue')
        print(cmd)
        with open("queue.sh", "a") as file_object:
            file_object.write(cmd+"\n")