#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os, subprocess, logging, argparse, sys

from fileprocessor import Fileprocessor

fileprocessor = Fileprocessor()

parser = argparse.ArgumentParser(
    description="upload photos of vehicle to Wikimedia Commons "
)
parser.add_argument("filepath")
parser.add_argument('-v','--vehicle', type=str, required=True, choices=['tram','trolleybus','bus', 'train','station'])
parser.add_argument('-s','--system', type=str, required=False, help='wikidata id or wikidata name of transport system. Not applied to "auto" ')
parser.add_argument('-c','--city', type=str, required='auto' in sys.argv or '-s' not in sys.argv, help='wikidata id or wikidata name of city for "auto" ')
parser.add_argument('-m','--model', type=str, required='station' not in sys.argv, help='wikidata id or wikidata name of vehicle model')
parser.add_argument('-r','--street', type=str, required=False, help='wikidata id or wikidata name of streer or highway')
parser.add_argument('-n','--number', type=str, required='station' not in sys.argv, help='vehicle number')
parser.add_argument('-ro','--route', type=str, required=False, help='vehicle route text')
parser.add_argument('-l','--line', type=str, required=False, help='railway line wikidata object')

parser.add_argument(
    "-dry", "--dry-run", action="store_const", required=False, default=False, const=True
)
parser.add_argument(
    "--verify", action="store_const", required=False, default=False, const=True, help='confirm generated captions before upload'
)

args = parser.parse_args()


logging.getLogger().setLevel(logging.DEBUG)

# ./upload-vehicle.py --vehicle tram --system 'Moscow tram' --model LM-99AE --street Q15994144 --number 3024 --dry imgs/t1

if os.path.isfile(args.filepath):
    files = [args.filepath]
    assert os.path.isfile(args.filepath)
elif os.path.isdir(args.filepath):
    files = os.listdir(args.filepath)
else:
    raise Exception("filepath should be file or directory")

files = [os.path.join(args.filepath, x) for x in files]

uploaded_paths = list()
for filename in files:
    if fileprocessor.check_exif_valid(filename):
        texts = fileprocessor.make_image_texts_vehicle(
            filename=filename,
            vehicle=args.vehicle, system=args.system, model=args.model, street=args.street,
            route = args.route,
            number = args.number,
            city = args.city,
            country='Russia',
            line = args.line,
            
        )
        

        if args.dry_run:
            print()
            print('new commons file name: '+texts["name"])
            print(texts["text"])
            continue

        wikidata_list = list()
        wikidata_list+=texts['structured_data_on_commons']

        fileprocessor.upload_file(
            filename, texts["name"], texts["text"], verify_description=args.verify
        )
        fileprocessor.append_image_descripts_claim(texts["name"], wikidata_list)
        uploaded_paths.append('https://commons.wikimedia.org/wiki/File:'+texts["name"].replace(' ', '_'))
    else:
        fileprocessor.logger.warning('can not open file '+filename+', skipped')
        continue
        
if len(uploaded_paths)>1:    
    print('Uploaded:')
    for element in uploaded_paths:
        print(element)
elif len(uploaded_paths)==1:
    print('Uploaded '+uploaded_paths[0])