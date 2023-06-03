#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os, subprocess, logging, argparse, sys

from model_wiki import Model_wiki



parser = argparse.ArgumentParser(
    description="maintain photos of user in Wikimedia Commons "
)

parser.add_argument(
    "-dry", "--dry-run", action="store_const", required=False, default=False, const=True
)


args = parser.parse_args()


logging.getLogger().setLevel(logging.DEBUG)

modelwiki = Model_wiki()

logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
modelwiki.create_category_taken_on_day('Moscow','2023-05-31')
#modelwikidata.create_category_taken_on_day('Moscow','2023-03-30')