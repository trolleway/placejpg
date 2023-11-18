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
    description="Create category in Wikimedia Commons for vehicle/number"
)

parser.add_argument("number")
parser.add_argument('-v', '--vehicle', type=str, required=True, choices=[
                    'tram', 'trolleybus', 'bus', 'train', 'locomotive', 'station', 'auto'])
parser.add_argument('-m', '--model_name', type=str, required=False, help='string name of model for category')
parser.add_argument('-c', '--city_name', type=str, required=False, help='string name of city for category')

args = parser.parse_args()

desc_dict = dict()
desc_dict['number'] = args.number
desc_dict['vehicle'] = args.vehicle
desc_dict['city_name'] = args.city_name
desc_dict['model_name'] = args.model_name

if desc_dict['city_name']  != '' and desc_dict['model_name'] != '':
    
    modelwiki.create_vehicle_in_city_category(vehicle=desc_dict['vehicle'], number=desc_dict['number'],city_name=desc_dict['city_name'],model_name=desc_dict['model_name'])
else:
    modelwiki.create_number_on_vehicles_category(vehicle=desc_dict['vehicle'], number=desc_dict['number'])
