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
parser.add_argument(
    "action",   choices=['taken']
)
parser.add_argument(
    "--url",  required=False, default=False
)
parser.add_argument(
    "--category",  required=False, default=False
)

parser.add_argument(
    "--location",  required=False, default=False
)
parser.add_argument(
    "--interactive",  required=False, default=False, action="store_const",  const=True
)

args = parser.parse_args()


logging.getLogger().setLevel(logging.DEBUG)

modelwiki = Model_wiki()

logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
if args.action == 'taken':
    if args.url:
        modelwiki.url_add_template_taken_on(args.url,args.location,dry_run=args.dry_run)
    if args.category:

        modelwiki.category_add_template_taken_on(args.category,args.location,dry_run=args.dry_run,interactive = args.interactive)

    
    
    
    
#modelwiki.create_category_taken_on_day('Moscow','2008-08-02')
#modelwiki.create_category_taken_on_day('Moscow','2004-07-17')
#modelwikidata.create_category_taken_on_day('Moscow','2023-03-30')

quit()
'''

python3 maintainer.py taken --location Moscow --url "https://commons.wikimedia.org/wiki/File:Moscow_trolleybus_202_2006-07_KTG-1_overhead_wire_control_2.jpg" -dry

'''

text = '''== {{int:filedesc}} ==
{{Information
| Description = ZiU-682GM1. Peschanaya ploshad, houses build circa 1955-1958.
| Source      = [https://www.flickr.com/photos/trolleway/14430752056/ Moscow trolleybus 1710 Песчаная площадь]
| Date        = 2014-04-27 17:25
| Author      = [https://www.flickr.com/people/24415554@N04 Artem Svetlov] from Moscow, Russia
| Permission  = 
| other_versions=
}}
{{Location dec|55.793861|37.510047|source:Flickr}}

=={{int:license-header}}==
{{cc-by-2.0}}
{{User:FlickreviewR/reviewed-pass|trolleway|https://www.flickr.com/photos/24415554@N04/14430752056|2015-06-05 09:41:28|cc-by-2.0|}}
[[Category:Photographs by Artem Svetlov/Moscow]]
[[Category:Mosgortrans trolleybuses]]
'''
text = modelwiki.atto(text,'Moscow')

print(text)