#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, subprocess, logging, argparse, sys, pprint, datetime
import pywikibot

import trolleway_commons
from model_wiki import Model_wiki
from fileprocessor import Fileprocessor
from urllib.parse import urlparse
import csv
from tqdm import tqdm


parser = argparse.ArgumentParser(
    description="Set SDC for all files in Commons category of this wikidada entiti")

parser.add_argument('--wikidata', type=str, required=True)


class Helper_SDC:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger(__name__)
    pp = pprint.PrettyPrinter(indent=4)
    
    cachedir='maintainer_cache'
    fileprocessor = Fileprocessor()



if __name__ == '__main__':
    
    args = parser.parse_args()
    processor = trolleway_commons.CommonsOps()
    modelwiki = Model_wiki()
    helper_renamer = Helper_SDC()

    wikidata = modelwiki.wikidata_input2id(args.wikidata)
    
   
    pagenames = modelwiki.list_category_by_wikidata(wikidata)
    
    
    entity_list = modelwiki.wikidata2instanceof_list(wikidata)
    entity_list.append(wikidata)
    for pagename in pagenames:
        print(pagename,entity_list)
        for wdid in entity_list:
            wd=modelwiki.get_wikidata_simplified(wdid)
            print(' -- '+wd['labels']['en'])
    for pagename in tqdm(pagenames):
        modelwiki.append_image_descripts_claim(pagename,entity_list)
    
    

    
        