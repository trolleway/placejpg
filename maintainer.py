#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os, subprocess, logging, argparse, sys

from model_wiki import Model_wiki
import trolleway_commons


parser = argparse.ArgumentParser(
    description="maintain photos of user in Wikimedia Commons "
)

parser.add_argument(
    "-dry", "--dry-run", action="store_const", required=False, default=False, const=True
)
parser.add_argument("action", choices=["taken", "dev", "panoramio_replace"])
parser.add_argument("--url", required=False, default=False)
parser.add_argument("--category", required=False, default=False)

parser.add_argument("--location", required=False, default=False)
parser.add_argument(
    "--interactive", required=False, default=False, action="store_const", const=True
)
parser.add_argument("--pagename", required=False, default=False)
parser.add_argument("--filename", required=False, default=False)

args = parser.parse_args()


logging.getLogger().setLevel(logging.DEBUG)

modelwiki = Model_wiki()
modelwiki1 = trolleway_commons.CommonsOps()

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
if args.action == "taken":
    if args.url:
        modelwiki.url_add_template_taken_on(
            args.url, args.location, dry_run=args.dry_run
        )
    if args.category:

        modelwiki.category_add_template_taken_on(
            args.category,
            args.location,
            dry_run=args.dry_run,
            interactive=args.interactive,
        )

if args.action == "dev":

    # from fileprocessor import Fileprocessor

    # fileprocessor = Fileprocessor()
    obj_wdid = modelwiki.wikidata_input2id(str("Дача").strip())
    loc_wdid = modelwiki.wikidata_input2id(str("Кратово").strip())
    print(modelwiki.get_category_object_in_location(obj_wdid, loc_wdid))
