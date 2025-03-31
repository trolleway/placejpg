#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, subprocess, logging, argparse, sys, pprint, datetime

import trolleway_commons
from model_wiki import Model_wiki
from fileprocessor import Fileprocessor
from urllib.parse import urlparse


import pywikibot
from pywikibot import pagegenerators
from pywikibot import exceptions

parser = argparse.ArgumentParser(
    description="For wikidata object with Cultural Heritage Russia number and category: move files from old category to this object category")

parser.add_argument('category', type=str,  help='Commons category from ')
parser.add_argument('wikidata', type=str,  help='wikidata entity for object with russian cultural heritage number')



if __name__ == '__main__':
    
    args = parser.parse_args()
    processor = trolleway_commons.CommonsOps()
    modelwiki = Model_wiki()
    
    site = pywikibot.Site("commons", "commons")
    site.login()
    site.get_tokens("csrf")  # preload csrf token
    
    heritage_wdid = args.wikidata
    heritage_wd = modelwiki.get_wikidata_simplified(heritage_wdid)
    if heritage_wd["commons"] is None:
        print('no commons in this wikidata')
        quit()
    russian_cultural_heritage_id = modelwiki.get_best_claim(heritage_wdid, "P1483")
    
    
    categoryname=f"WLM/{russian_cultural_heritage_id}"
    category = pywikibot.Category(site, categoryname)

    gen1 = pagegenerators.CategorizedPageGenerator(
        category,
        recurse=0,
        start=0,
        content=True,
        namespaces=None,
    )
    
    old_category = args.category
    new_category = heritage_wd["commons"]
    for file_page in gen1:
        print(file_page.title().replace("File:", ""))
        
        text = file_page.text

        # Replace the old category with the new one
        updated_text = text.replace(f"[[Category:{old_category}]]", f"[[Category:{new_category}]]")

        # Save the updated description
        if text != updated_text:
            modelwiki.difftext(text, updated_text)
    

    print("Press Enter to continue or Ctrl+C for cancel...")
    input()

    del gen1
    gen1 = pagegenerators.CategorizedPageGenerator(
        category,
        recurse=0,
        start=0,
        content=True,
        namespaces=None,
    )
    for file_page in gen1:     
        text = file_page.text
        # Replace the old category with the new one
        updated_text = text.replace(f"[[Category:{old_category}]]", f"[[Category:{new_category}]]")
        # Save the updated description
        if text != updated_text:        
            file_page.text = updated_text
            file_page.save(summary=f"Changing category from '{old_category}' to '{new_category}'")


    
        