#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, subprocess, logging, argparse, sys, pprint, datetime

import trolleway_commons
from model_wiki import Model_wiki
from fileprocessor import Fileprocessor
from urllib.parse import urlparse


import pywikibot

parser = argparse.ArgumentParser(
    description=" ")

parser.add_argument('category', type=str,  help='Commons category')



if __name__ == '__main__':
    
    args = parser.parse_args()
    processor = trolleway_commons.CommonsOps()
    modelwiki = Model_wiki()
    
    modelwiki.print_category_filenames(args.category)
        

    
        