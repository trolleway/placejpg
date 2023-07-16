#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os, subprocess, logging, argparse, sys

import trolleway_commons
from model_wiki import Model_wiki

parser = argparse.ArgumentParser(
    description="Create building entity in Wikidata and Wikimedia Commons "+''' 
    useful maps:
    get coords https://wikivoyage.toolforge.org/w/geomap.php?lang=ru
    dates https://flatinfo.ru/h_info1.asp?hid=189602
    wikidata objects https://wikishootme.toolforge.org/#lat=55.77&lng=37.66&zoom=18
    
    
    '''
)
sample_expression ='''

'python3 add-building.py --coords "' ||  round(y(point_on_surface(@geometry)),5) || ' ' || round(x(point_on_surface(@geometry)),5)|| '" --city   --street '||  "osm — lines_wikidata"  ||' -n '||  "addr_housenumber" || ' --coord_source osm ' 

'''
parser.add_argument('--city', type=str, required=True, help='City name string')
parser.add_argument('--street', type=str, required=True, help='Street wikidata entity. Can bu wikidata id, wikidata url, wikidata name')
parser.add_argument('-n','--housenumber', type=str, required=True, help='housenumber')
parser.add_argument('-c','--coords', type=str, required=True, help='latlong string in EPSG:4326. Separators: " ", | ,')
parser.add_argument('-cs','--coord_source', type=str, required=True, choices=['osm','yandex maps','reforma'], help='internet project - source of coordinates')
parser.add_argument('--levels', type=int, required=False, help='Building levels count')
parser.add_argument('--levels_url', type=str, required=False, help='url for building levels refrence')
parser.add_argument('--year', type=int, required=False, help='year built')
parser.add_argument('--year_url', type=str, required=False, help='url for year refrence')
parser.add_argument("--country", type=str,required=False, default='Russia', help='Country for {{Taken on}} template')
parser.add_argument('--photos', type=str, required=False, help='Optional: call photo uploader , path to files dir ')

parser.add_argument(
    "-dry", "--dry-run", action="store_const", required=False, default=False, const=True
)

args = parser.parse_args()
processor = trolleway_commons.CommonsOps()
modelwiki = Model_wiki()

buildings = list()
building = {
        "housenumber": str(args.housenumber),
        "street_wikidata": processor.wikidata_input2id(str(args.street).strip()),
        "latlonstr": args.coords,
        "coord_source": args.coord_source,
        'city':args.city,
        }
        
if args.levels: building['levels'] = args.levels            
if args.levels_url: building['levels_url'] = args.levels_url               
if args.year: building['year'] = args.year            
if args.year_url: building['year_url'] = args.year_url            
if args.photos: building['files_dir'] = args.photos            
if args.photos: assert os.path.exists(args.photos)        
        


buildings.append(building)

validation_pass = True
for data in buildings:
    if processor.validate_street(data) == False:
        validation_pass = False
print('validation ok')

if not validation_pass:
    print("street wikidata objects non valid")
    quit()
for data in buildings:
    building_wikidata = modelwiki.create_wikidata_building(data, dry_mode=args.dry_run)
    category_name = processor.create_commonscat(
        building_wikidata, city_en=args.city, dry_mode=args.dry_run,
        
    )
    print('Created https://www.wikidata.org/wiki/'+building_wikidata)
    print('Created https://commons.wikimedia.org/wiki/Category:'+category_name.replace(' ','_'))
    print('Created https://commons.wikimedia.org/wiki/Category:'+category_name.replace(' ','_'))
    if args.photos:
        cmd = ['python3','building-upload.py', building_wikidata, args.photos, '--country',args.country]
        response = subprocess.run(cmd) 