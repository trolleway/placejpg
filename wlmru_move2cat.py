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
import logging
logging.disable(level=logging.WARNING)  # Disable WARNING-level logs

parser = argparse.ArgumentParser(
    description="For wikidata object with Cultural Heritage Russia number and category: move files from old category to this object category")
subparsers = parser.add_subparsers(help='command')

parser_mv = subparsers.add_parser('mv', help='move file from some CATEGORY to specific category for WIKIDATA entity')
parser_mv.add_argument('wikidata', type=str,  help='wikidata entity for object with russian cultural heritage number')
parser_mv.add_argument('category', type=str, nargs='+', help='Commons category FROM')
parser_mv.add_argument('--building-category', action='store_true',  help='create building category if needed')
parser_mv.add_argument('--city', type=str, required='--building-category' in sys.argv, help='city wdid for create a building category')
parser_mv.set_defaults(cmd='mv')

parser_validator = subparsers.add_parser('validator', help='print heritage objects WIKIDATA entities for witch a category can be created and populated at lest 2 exist files in large CATEGORY')
parser_validator.add_argument('category', type=str,  help='Commons category from ')
parser_validator.add_argument('wikidata', type=str,  help='wikidata entity for administrative district', default='Q1829')

parser_validator.set_defaults(cmd='validator')


parser_validator_street_hasnot_category = subparsers.add_parser('validator_streets_hasnot_category', help='print list of STREETS witch has a category but has not WIKIDATA')
parser_validator_street_hasnot_category.add_argument('category', type=str,  help='Commons category from ')


parser_validator_street_hasnot_category.set_defaults(cmd='validator_streets_hasnot_category')


if __name__ == '__main__':
    
    args = parser.parse_args()
    processor = trolleway_commons.CommonsOps()
    modelwiki = Model_wiki()
    
    site = pywikibot.Site("commons", "commons")
    site.login()
    site.get_tokens("csrf")  # preload csrf token
    if args.cmd == 'validator_streets_hasnot_category':
    
        parent_category_obj = pywikibot.Category(site, args.category)
        for subcat in parent_category_obj.subcategories(recurse=False):
            #print(f"Subcategory: {subcat.title()}")
            title=subcat.title()
            try:
                # Attempt to retrieve the associated Wikidata item.
                wikidata_item = subcat.data_item()
                if wikidata_item and wikidata_item.exists():
                    pass
                    #print(f"  Wikidata ID: {wikidata_item.getID()}")
                else:
                    print(subcat.title())
                    #print("  No associated Wikidata item found")
            except Exception as e:
                
                print(subcat.title())
                #print(f"  Error retrieving Wikidata item: {e}")    
    '''
    
    
    import pywikibot

def main():
    # Connect to Wikimedia Commons.
    site = pywikibot.Site('commons', 'commons')
    
    # Define the parent category.
    # Change "Streets in Kallingrad" to your desired category name.
    # Note: Wikimedia Commons categories use the "Category:" prefix.
    parent_category_title = "Category:Streets in Kallingrad"
    parent_category = pywikibot.Category(site, parent_category_title)
    
    # Iterate over subcategories (one level).
    for subcat in parent_category.subcategories(recurse=False):
        print(f"Subcategory: {subcat.title()}")
        try:
            # Attempt to retrieve the associated Wikidata item.
            wikidata_item = subcat.data_item()
            if wikidata_item and wikidata_item.exists():
                print(f"  Wikidata ID: {wikidata_item.getID()}")
            else:
                print("  No associated Wikidata item found")
        except Exception as e:
            print(f"  Error retrieving Wikidata item: {e}")

if __name__ == "__main__":
    main()

'''
    
    if args.cmd == 'validator':


        sitewikidata = pywikibot.Site("wikidata", "wikidata")
        repowikidata = site.data_repository()

        sparql = """
SELECT ?item ?englishName ?russianName ?coordinates ?directions ?street ?houseNumber ?commonsSitelink ?P1483 WHERE {
  ?item wdt:P131 wd:Q1829.  # Items located in CITY (Q1829)

  OPTIONAL { ?item rdfs:label ?englishName FILTER(LANG(?englishName) = "en"). }
  OPTIONAL { ?item rdfs:label ?russianName FILTER(LANG(?russianName) = "ru"). }
  OPTIONAL { ?item wdt:P625 ?coordinates. }  # Coordinates
  OPTIONAL { ?item wdt:P2795 ?directions. }   # Directions
  OPTIONAL { ?item wdt:P669 ?street. }       # Located on street
  OPTIONAL { ?item wdt:P670 ?houseNumber. }  # House number
  OPTIONAL { ?item wdt:P373 ?commonsSitelink. }  # Commons sitelink
  { ?item wdt:P1483 ?P1483. }       # russian heritage number

}
  ORDER BY ?directions
  
"""
        sparql = sparql.replace('Q1829',args.wikidata)
        generator = pagegenerators.PreloadingEntityGenerator(
            pagegenerators.WikidataSPARQLPageGenerator(sparql, site=repowikidata)
        )
        items_ids = list()
        old_category = args.category
        
        old_category_pywikibotobj=pywikibot.Category(site, old_category)

        counter=0
        for item in generator:
            counter=counter+1
            #print(counter)
            items_ids.append(item.id)
            
            #get russian heritage id
            
            #russian_cultural_heritage_id = item.claims.get('P1483', None)
            russian_cultural_heritage_id = modelwiki.get_best_claim(str(item.id), "P1483")
            categoryname=f"WLM/{russian_cultural_heritage_id}"
            category = pywikibot.Category(site, categoryname)

            gen1 = pagegenerators.CategorizedPageGenerator(
                category,
                recurse=0,
                start=0,
                content=True,
                namespaces=None,
            )
            #filesfound=len(list(gen1))
            #if filesfound < 2: continue
            #print(f"in {category} found files:{filesfound}")
            filesfound=0
            
            for file_page in gen1:
                #print(file_page.title().replace("File:", ""))
                text = file_page.text
                if old_category.upper().replace(' ','_') in file_page.text.upper().replace(' ','_'):
                    filesfound = filesfound+1
  
            if filesfound < 2: continue
            addr=modelwiki.get_best_claim(str(item.id), "P2795") #directions
            
            building_wd= modelwiki.get_wikidata_simplified(str(item.id))
            commons=building_wd['commons']
            #print(str(counter)+'--------- https://www.wikidata.org/wiki/'+str(item.id)+'  '+item.labels.get('en', item.labels.get('ru','хз')) +' '+ str(filesfound))
            name=item.labels.get('en', item.labels.get('ru','хз'))
            line=addr[:30].ljust(30) + ' '+str(counter).zfill(4)+' '+str('https://www.wikidata.org/wiki/'+str(item.id)).ljust(37) +' '+ name[:45].rjust(45)+ ' ['+ str(filesfound).zfill(2)+'] '+ commons[5:20].rjust(20)
            print(line)
            
            #print(f"Pages in {old_category} for {russian_cultural_heritage_id}: {filesfound}")

            del gen1
        
    
    
    if args.cmd == 'mv':

        heritage_wdid = args.wikidata
        city_wdid = args.city
        if args.building_category:
            cmd = f'./add-building.py --city {city_wdid} --wikidata {heritage_wdid}'
            os.system(cmd)
        heritage_wd = modelwiki.get_wikidata_simplified(heritage_wdid)
        if heritage_wd["commons"] is None:
            print('no commons in this wikidata')
            quit()
        russian_cultural_heritage_id = modelwiki.get_best_claim(heritage_wdid, "P1483")
        categoryname=f"WLM/{russian_cultural_heritage_id}"
        category = pywikibot.Category(site, categoryname)

        for old_category in args.category:
            gen1 = pagegenerators.CategorizedPageGenerator(
                category,
                recurse=0,
                start=0,
                content=True,
                namespaces=None,
            )
            
        
            new_category = heritage_wd["commons"]
            diffscount = 0
            for file_page in gen1:
                print(file_page.title().replace("File:", ""))
                
                text = file_page.text

                # Replace the old category with the new one
                updated_text = text.replace(f"[[Category:{old_category}]]", f"[[Category:{new_category}]]")

                # Save the updated description
                if text != updated_text:
                    modelwiki.difftext(text, updated_text)
                    diffscount = diffscount+1
            
            if diffscount == 0: continue
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


