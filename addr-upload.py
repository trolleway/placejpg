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
    description="upload photos of building to wikimedia commons. Photo must has _place key in name for street/district, and building address will taken from gpkg file. If more than 1 photo of same building, create wikidata object for building and use instead upload.py "
)

parser.add_argument("filepath")
parser.add_argument("--city_polygons", required=True)
parser.add_argument("--street_polygons", required=True)
parser.add_argument("--addr_polygons", required=True)


parser.add_argument(
    "--progress",
    required=False,
    action="store_const",
    default=False,
    help="display progress bar for folder upload",
    const=True,
)


parser.add_argument(
    "-dry", "--dry-run", action="store_const", required=False, default=False, const=True
)

args = parser.parse_args()

desc_dict = dict()
desc_dict["mode"] = "addr"
desc_dict["city_polygons"] = args.city_polygons
desc_dict["street_polygons"] = args.street_polygons
desc_dict["addr_polygons"] = args.addr_polygons
desc_dict["wikidata"] = "trolleybus.gpkg"
desc_dict["progress"] = args.progress


desc_dict["dry_run"] = args.dry_run


fileprocessor.process_and_upload_files(args.filepath, desc_dict)
