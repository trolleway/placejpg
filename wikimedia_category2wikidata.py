#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os, subprocess, logging, argparse
import sys
 
from model_wiki import Model_wiki



parser = argparse.ArgumentParser(
    description='''For exist Wikimedia commons category like "Shops in Russia" create wikidata entity, so when upload file with place somewhere in Russia and shop, it taken into this category
    
    python3 wikimedia_category2wikidata.py 'Category:Buttresses in Russia' Q331900 Q159
    '''
)



parser.add_argument('category', type=str,  help='wikimedia category')
parser.add_argument('wikidata1', type=str,  help='abstract entity')
parser.add_argument('wikidata2', type=str,  help='location entity')


args = parser.parse_args()
modelwiki = Model_wiki()



modelwiki.create_wikidata_object_for_bylocation_category(args.category,args.wikidata1,args.wikidata2)