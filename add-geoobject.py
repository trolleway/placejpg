#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os, subprocess, logging, argparse, sys
import shortuuid

import trolleway_commons
from model_wiki import Model_wiki



parser = argparse.ArgumentParser(
    description="Create geoobject entity in Wikidata and Wikimedia Commons. Something with coordinates except building and did not have street address ")



parser.add_argument('--wikidata', type=str, required=False, help='Wikidata object if already exists')
parser.add_argument('--maintype', type=str, required=False, default='Q79007', help='Wikidata instanceof for creating a new object: street, pond, park')

parser.add_argument('--name_en', type=str, required=False, help='English street name')
parser.add_argument('--name_ru', type=str, required=False, help='Russian street name')
parser.add_argument('--city', type=str, required=False, default=None, help='City wikidata entity. When not set, will be searched in "administrative entity" in wikidata. Can be wikidata id, wikidata url, wikidata name')
parser.add_argument('--district', type=str, required=False, help='Administrative entity wikidata entity. Can be wikidata id, wikidata url, wikidata name')

parser.add_argument('--country', type=str, required=False, help='Country name string or wikidata link')
parser.add_argument('--named_after', type=str, required=False, help='Named after string or wikidata link')
parser.add_argument('-c','--coords', type=str, required='wikidata' in sys.argv, help='WKT linestring or latlong string in EPSG:4326. Separators: " ", | ,')
parser.add_argument('--wikidata-only', action="store_const", const=True, required=False, help='Create only wikidata entity, do not create commons category ')
parser.add_argument('--catname', required=False, default=None, help='commons category for this street if exist')

#parser.add_argument('--wikidata-only', action="store_const", const=True, required=False, help='Create only wikidata entity, do not create commons category ')
#required='wikidata' not in sys.argv

parser.add_argument(
    "-dry", "--dry-run", action="store_const", required=False, default=False, const=True
)

args = parser.parse_args()
wdid = args.wikidata
if wdid is None:
    # generate UUID as early as possible 
    local_wikidata_uuid='UUID'+str(shortuuid.uuid())
    print(f'Created UUID, you now can use it as placeholder for wikidata id place in filename')
    print(local_wikidata_uuid)
else:
    local_wikidata_uuid = None

processor = trolleway_commons.CommonsOps()
modelwiki = Model_wiki()

coords = args.coords
catname = args.catname

city = args.city
district = args.district


# --- move to method

modelwiki.create_or_update_geoobject(city_wdid=modelwiki.wikidata_input2id(args.city), 
country_wdid = modelwiki.wikidata_input2id(args.country), 
named_after_wdid = modelwiki.wikidata_input2id(args.named_after),
street_name_en = args.name_en,
street_name_ru = args.name_ru,
maintype=args.maintype,
wikidata_only =  args.wikidata_only,
catname = catname,
wdid=wdid,
coords=coords,
district=district,

local_wikidata_uuid=local_wikidata_uuid)