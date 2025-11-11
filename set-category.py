#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, subprocess, logging, argparse, sys, pprint, datetime
import pywikibot

import trolleway_commons
from model_wiki import Model_wiki
from urllib.parse import urlparse


parser = argparse.ArgumentParser(
    description=" ")

group = parser.add_mutually_exclusive_group()

group.add_argument('wdabstract', type=str, required=False, help='Wikipedia filepage')
group.add_argument('wdobject', type=str, required=False, help='Wikipedia filepage')






if __name__ == '__main__':
    
    args = parser.parse_args()
    modelwiki = Model_wiki()



    r=modelwiki.get_category_object_in_location(args.wdabstract,args.wdobject)
    print(r)
    
    
    

#set category by 2 wikidata ids


modelwiki.get_category_object_in_location