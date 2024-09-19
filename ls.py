#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import subprocess
import logging
import argparse
import sys


from model_wiki import Model_wiki


parser = argparse.ArgumentParser(
    description="list filenames in Wikimedia Commons category"
)

parser.add_argument('category', type=str,  help='commons category')



args = parser.parse_args()

modelwiki = Model_wiki()
filenames = modelwiki.print_category_filenames(args.category)





"""

./ls.py "Category:Tifontai Trading House" | grep IMAG



"""