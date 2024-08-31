#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os, subprocess, logging, argparse, sys

import trolleway_commons
from model_wiki import Model_wiki



parser = argparse.ArgumentParser(
    description="For wikidata entity and place entity search category tree and print proposed new categories.")




parser.add_argument('-wd','--wikidata', required=True, help='wikidata object')
parser.add_argument('-p','--place', required=True, help='wikidata object for place')


parser.add_argument(
    "-dry", "--dry-run", action="store_const", required=False, default=False, const=True
)

args = parser.parse_args()
processor = trolleway_commons.CommonsOps()
modelwiki = Model_wiki()

object_wdid = modelwiki.wikidata_input2id(args.wikidata)
location_wdid = modelwiki.wikidata_input2id(args.place)

text, proposeds = modelwiki.category_tree_upwalk(object_wdid, location_wdid, order = None, verbose=True)

object_wd = modelwiki.get_wikidata_simplified(object_wdid)
object_commonscat = object_wd['commons']


if len(proposeds)>0:
    for proposed_cat in proposeds:

        location_wd = modelwiki.get_wikidata_simplified(proposed_cat['location_wdid'])
        location_commonscat = location_wd.get('commons','')
        if location_commonscat is None: location_commonscat = ''
        
        upper_location_wd=modelwiki.get_wikidata_simplified(proposed_cat['upper_location_wdid'])
        location_upper_commonscat = upper_location_wd.get('commons',' no commons name ')
        if location_upper_commonscat is None:
            print()
            print('go to next level')
            continue
        
        print()
        print(proposed_cat['name'])
        print('{{Wikidata Infobox}}')
        print('{{GeoGroup}}')
        print('[[Category:'+object_commonscat+' in '+str(location_upper_commonscat) +']]')
        print('[[Category:'+location_commonscat+']]')
        