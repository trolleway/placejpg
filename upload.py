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
parser.add_argument("-dry", "--dry-run", action="store_const", required=False, default=False, const=True)
parser.add_argument("-l", "--later", action="store_const", required=False, default=False, help='add to job list for upload later', const=True)
parser.add_argument(
    "--verify", action="store_const", required=False, default=False, const=True
)
parser.add_argument("--location", type=str,required=False, default='Russia', help='Country for {{Taken on}} template')
parser.add_argument('-s',"--secondary-objects", type=str, nargs='+',required=False,  help='secondary wikidata objects, used in category calc with country')
parser.add_argument("--rail", action="store_const", required=False, default=False, const=True, help='add to https://commons.wikimedia.org/wiki/Category:Railway_photographs_by_date')
parser.add_argument(
    "--building",
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


#wikidata = fileprocessor.take_user_wikidata_id(fileprocessor.prepare_wikidata_url(args.wikidata))
from model_wiki import Model_wiki
modelwiki = Model_wiki()
wikidata = modelwiki.wikidata_input2id(args.wikidata)
secondary_wikidata_ids = modelwiki.input2list_wikidata(args.secondary_objects)

dry_run = args.dry_run
if args.later:dry_run = True

uploaded_paths = list()
for filename in files:
    if 'commons_uploaded' in filename: continue
    if fileprocessor.check_exif_valid(filename) and not args.later:
        
        if not args.building:
            
            texts = fileprocessor.make_image_texts_simple(
                filename=filename,
                wikidata=wikidata,
                country=args.location.capitalize(),
                rail=args.rail,
                secondary_wikidata_ids = secondary_wikidata_ids,
                quick=args.later
            )    
        else:
            
            texts = fileprocessor.make_image_texts_building(
                filename=filename,
                wikidata=wikidata,
                place_en="Moscow",
                place_ru="Москва",
                no_building= not args.building,
                country=args.location.capitalize(),
                rail=args.rail
            )

        if dry_run:
            print()
            print(texts["name"])
            print(texts["text"])


        wikidata_list = list()
        wikidata_list.append(wikidata)
        wikidata_list += secondary_wikidata_ids
        
        if not dry_run:
            fileprocessor.upload_file(
                filename, texts["name"], texts["text"], verify_description=args.verify
            )
            
            standalone_captions_dict = fileprocessor.make_image_texts_standalone(filename,wikidata,secondary_wikidata_ids)
            fileprocessor.copy_image4standalone(filename,standalone_captions_dict['new_filename'])
            fileprocessor.create_json4standalone(filename,standalone_captions_dict['new_filename'],standalone_captions_dict['ru'],standalone_captions_dict['en'])
            

        modelwiki.append_image_descripts_claim(texts["name"], wikidata_list, dry_run)
        if not dry_run:
            modelwiki.create_category_taken_on_day(args.location.capitalize(),texts['dt_obj'].strftime("%Y-%m-%d"))
        else:
            print('will append '+' '.join(wikidata_list))
            
        uploaded_paths.append('https://commons.wikimedia.org/wiki/File:'+texts["name"].replace(' ', '_'))
        
        if not dry_run:
            if not os.path.exists(uploaded_folder_path):
                os.makedirs(uploaded_folder_path)
            shutil.move(filename, os.path.join(uploaded_folder_path, os.path.basename(filename)))
   
    else:
        print('can not open file '+filename+', skipped')
        continue

if not dry_run:
    print('uploaded: ')
else:
    print('emulating upload. URL will be: ')

print("\n".join(uploaded_paths))

if dry_run:
    if not args.later:
        add_queue = input("Add to queue? Y/N    ")
    else:
        add_queue='Y'

    if add_queue.upper()=='Y':
        cmd = 'python3 upload.py '
        if args.building: cmd += '--building '
        cmd += wikidata + ' '
        cmd += '"'+args.filepath + '" '
        if args.location: cmd += '--location "'+ args.location + '" '
        if args.rail: cmd += ' --rail '
        if len(secondary_wikidata_ids)>0: cmd += '-s ' + ' '.join(secondary_wikidata_ids)
        
        print('adding to queue')
        print(cmd)
        with open("queue.sh", "a") as file_object:
            file_object.write(cmd+"\n")
    else:
        print('not adding to queue')
