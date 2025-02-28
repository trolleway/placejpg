#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os, subprocess, logging, argparse
import sys
 
from model_wiki import Model_wiki



parser = argparse.ArgumentParser(
    description='''change value in wikidata entity from optional old value to new

    '''
)



parser.add_argument('wikidata', type=str,  help='wikidata entity')
parser.add_argument('prop', type=str,  help='property')
parser.add_argument('editmessage', type=str,  help='edit message')
parser.add_argument('--vfrom', type=str, required=False, help='value change from')
parser.add_argument('--vto', type=str, required=True, help='value to')


args = parser.parse_args()
modelwiki = Model_wiki()



modelwiki.wikidata_change_claim(args.wikidata,args.prop,vfrom=args.vfrom,vto=args.vto,editmessage=args.editmessage)