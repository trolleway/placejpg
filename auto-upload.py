#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import subprocess
import logging
import argparse
import sys

from fileprocessor import Fileprocessor
from model_wiki import Model_wiki

fileprocessor = Fileprocessor()
modelwiki = Model_wiki()

parser = argparse.ArgumentParser(
    description="upload photos of vehicle to Wikimedia Commons. Sample filename: аа903 69_20120520_369_colorwhite_r2.JPG"
)

parser.add_argument("filepath")
parser.add_argument('-v', '--vehicle', type=str, required=True, choices=[
                    'bus', 'auto'])
parser.add_argument('-sys', '--system', type=str, required=False,
                    help='wikidata id or wikidata name of transport system. Not applied to "auto" ')
parser.add_argument('-c', '--city', type=str, required=False,
                    help='wikidata id or wikidata name of city for "auto" ')
parser.add_argument('-m', '--model', type=str, required=False,
                    help='wikidata id or wikidata name of vehicle model')
parser.add_argument('-st', '--street', type=str, default=None, required=False,
                    help='wikidata id or wikidata name of streer or highway')
parser.add_argument('--digital_number', type=str, required=False,
                    help='optional digit vehicle number for Wikimedia Commons category. Example: 1468 from 2TE10M-1468 ')
parser.add_argument('-ro', '--route', type=str,
                    required=False, help='vehicle route text')
parser.add_argument('-op', '--operator', type=str,
                    required=False, help='vehicle operator')
parser.add_argument('-opc', '--operator-vehicle-category', type=str,
                    required=False, help='commons category for vehicle operator like Operatorname buses')
parser.add_argument('--line', type=str, required=False,
                    help='railway line wikidata object for trains')
parser.add_argument("--country", type=str, required=True,
                    default='Russia', help='Country for {{Taken on}} template')
parser.add_argument('--facing', type=str, required=False,  choices=['Left', 'Right', 'Front', 'Rear',
                    'Side', 'Three-quarter', 'Rear three-quarter'], help='puts in [[Category:Trolleybuses facing left]]')
parser.add_argument('--colors', type=str, nargs='+', required=False,
                    help='puts in [[Category:Green and yellow trams]]')
parser.add_argument('-s', "--secondary-objects", type=str, nargs='+', required=False,
                    help='secondary wikidata objects, used in category calc with country')
parser.add_argument("--progress", required=False, action="store_const",
                    default=False, help='display progress bar for folder upload', const=True)

parser.add_argument(
    "-dry", "--dry-run", action="store_const", required=False, default=False, const=True
)
parser.add_argument("-l", "--later", action="store_const", required=False,
                    default=False, help='add to job list for upload later', const=True)
parser.add_argument("--verify", action="store_const",
                    required=False, default=False, const=True)

args = parser.parse_args()

desc_dict = dict()
desc_dict['mode'] = args.vehicle
desc_dict['vehicle'] = args.vehicle
desc_dict['system'] = args.system
desc_dict['city'] = args.city
desc_dict['model'] = args.model
desc_dict['street'] = args.street
desc_dict['operator'] = args.operator
desc_dict['operator_vehicle_category'] = args.operator_vehicle_category
desc_dict['digital_number'] = args.digital_number
desc_dict['route'] = args.route
desc_dict['line'] = args.line
desc_dict['country'] = args.country
desc_dict['facing'] = args.facing
desc_dict['colors'] = args.colors
desc_dict['progress'] = args.progress

desc_dict['secondary_objects'] = args.secondary_objects or None

desc_dict['later'] = args.later
desc_dict['dry_run'] = args.dry_run


fileprocessor.process_and_upload_files(args.filepath, desc_dict)
