#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, subprocess, logging, argparse, sys, pprint, datetime
import pywikibot

import trolleway_commons
from model_wiki import Model_wiki
from fileprocessor import Fileprocessor
from urllib.parse import urlparse


parser = argparse.ArgumentParser(
    description=" ")

parser.add_argument('--pagename', type=str, required=True, help='Wikipedia filepage')
parser.add_argument('--location', type=str, required=True)




if __name__ == '__main__':
    
    args = parser.parse_args()
    processor = trolleway_commons.CommonsOps()
    modelwiki = Model_wiki()


    pagename=args.pagename
    
    modelwiki.url_add_template_taken_on(pagename=pagename, location=args.location,verbose=True)
    
    