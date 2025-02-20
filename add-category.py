#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os, subprocess, logging, argparse, sys

import trolleway_commons
from model_wiki import Model_wiki
from simple_term_menu import TerminalMenu



parser = argparse.ArgumentParser(
    description="Create Wikimedia Commons category for Wikidata object")



parser.add_argument('wikidata', type=str,  help='Wikidata object')




group = parser.add_mutually_exclusive_group()
group.add_argument('--verify', action='store_true', help='Enable verify mode')
group.add_argument('--no-verify', action='store_true', help='Disable verify mode')
parser.add_argument('--suffix', type=str, required=False,default='')
args = parser.parse_args()
processor = trolleway_commons.CommonsOps()
modelwiki = Model_wiki()

wdid = args.wikidata

def user_select( candidates):
    i = 0
    for element in candidates:
        print(str(i).rjust(3)+': '+element)
        i = i+1
    print('Enter a number:')
    result = input()
    return int(result.strip())

def ask_for_confirmation():
    print("Do you want to continue? [y/n]")
    yes = {'yes','y', 'ye', ''}
    no = {'no','n'}

    choice = input().lower()
    if choice in yes:
       return True
    elif choice in no:
       return False
    else:
       sys.stdout.write("Please respond with 'y' or 'n'")
       quit()
# create category

is_make_variants=True



catname, content = modelwiki.make_catagory_texts_by_wikidata(wdid,suffix=args.suffix)



if args.no_verify == False:
    print
    print('creating category with content:')
    print(content)
    if is_make_variants:
        administrative_names = modelwiki.get_administrative_names_for_object(wdid, verbose=False)
        catname_variants=list()
        catname_variants.append(catname)
        for name in administrative_names:
            catname_variants.append(catname+', '+name)
        
        for catname_variant in catname_variants:
            if modelwiki.is_category_exists(catname_variant):
                print('category already exists: '+catname_variant)
                catname_variants.remove(catname_variant)
          
        if len(catname_variants) == 1:
            selected = catname_variants[0]
        else:
            try:
                terminal_menu = TerminalMenu(
                    catname_variants, title="Select name for category" )
                menu_entry_index = terminal_menu.show()
            except:
                # special for run in temmux
                menu_entry_index = user_select(catname_variants)
            selected = catname_variants[menu_entry_index]
        print('selected 【'+selected+'】')
        catname=selected
        

    #if not ask_for_confirmation():
    #    quit()


if not modelwiki.is_category_exists(catname):
    modelwiki.create_category(catname,content)
    modelwiki.wikidata_add_commons_category(wdid,catname)
else:
    print('category already exists')

print('created')
print(catname)