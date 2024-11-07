#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os, subprocess, logging, argparse, sys

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
processor = trolleway_commons.CommonsOps()
modelwiki = Model_wiki()
street_wdid = args.wikidata
coords = args.coords
catname = args.catname

city = args.city
district = args.district
dry_mode = args.dry_run

# --- move to method
def create_geoobject(city_wdid, country_wdid, named_after_wdid, street_name_en, street_name_ru, maintype, wikidata_only, catname, street_wdid):

    if street_wdid is None:
        street_wdid = modelwiki.create_geoobject_wikidata(city=city_wdid,
                                                       name_en=street_name_en,
                                                       name_ru =street_name_ru,
                                                       named_after=named_after_wdid, 
                                                       country=country_wdid, 
                                                       coords=coords,
                                                       maintype=maintype,
                                                       district=district,
                                                       dry_mode=dry_mode)
        if wikidata_only !=True and catname is None:
            street_category_result = modelwiki.create_category_by_wikidata(street_wdid, city_wdid)
            print(street_category_result)
        else:
            if catname is not None and modelwiki.is_category_exists(catname):
                modelwiki.wikidata_add_commons_category(street_wdid,catname)
                modelwiki.category_add_template_wikidata_infobox(catname)

    elif street_wdid is not None:
        
        street_wd = modelwiki.get_wikidata_simplified(street_wdid)
        # SET COORDINATES
        modelwiki.wikidata_set_coords(street_wdid,coords=coords)
        # CREATE CATEGORY IF NOT EXIST
        if street_wd['commons'] is None:
            # create street category
            street_category_result = modelwiki.create_category_by_wikidata(street_wdid, city_wdid)
            print(street_category_result)
        else:
            print('wikidata entity already has commons category')
        #add wikidata infobox if needed
        if catname is not None and modelwiki.is_category_exists(catname):
            modelwiki.category_add_template_wikidata_infobox(catname)
       
create_geoobject(city_wdid=modelwiki.wikidata_input2id(args.city), country_wdid = modelwiki.wikidata_input2id(args.country), 
named_after_wdid = modelwiki.wikidata_input2id(args.named_after),
street_name_en = args.name_en,
street_name_ru = args.name_ru,
maintype=args.maintype,
wikidata_only =  args.wikidata_only,
catname = catname,
street_wdid=street_wdid)