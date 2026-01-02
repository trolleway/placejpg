#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, subprocess, logging, argparse, sys, pprint, datetime
import pywikibot

import trolleway_commons
from model_wiki import Model_wiki
from urllib.parse import urlparse


parser = argparse.ArgumentParser(
    description=" ")


parser.add_argument('wdabstract', type=str, help='Wikipedia filepage')
parser.add_argument('wdobject', type=str,  help='Wikipedia filepage')






if __name__ == '__main__':
    
    args = parser.parse_args()
    modelwiki = Model_wiki()



    r=modelwiki.get_category_object_in_location(modelwiki.wikidata_input2id(args.wdabstract),modelwiki.wikidata_input2id(args.wdobject),verbose=True)
    print(r)
    
    
    
