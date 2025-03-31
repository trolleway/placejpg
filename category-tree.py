#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os, subprocess, logging, argparse, sys

import trolleway_commons
from model_wiki import Model_wiki
from simple_term_menu import TerminalMenu


parser = argparse.ArgumentParser(
    description="For wikidata entity and place entity search category tree and print proposed new categories."
)


parser.add_argument("wikidata", help="wikidata object")
parser.add_argument("place", help="wikidata object for place")
parser.add_argument("--country", required=False, help="Country wikidata or name for create category [Wikidata object] in [country]")


parser.add_argument(
    "-dry", "--dry-run", action="store_const", required=False, default=False, const=True
)

args = parser.parse_args()
processor = trolleway_commons.CommonsOps()
modelwiki = Model_wiki()

object_wdid = modelwiki.wikidata_input2id(args.wikidata)
location_wdid = modelwiki.wikidata_input2id(args.place)

text, proposeds = modelwiki.category_tree_upwalk(
    object_wdid, location_wdid, order=None, verbose=True
)

object_wd = modelwiki.get_wikidata_simplified(object_wdid)
object_commonscat = object_wd["commons"]

proposed_cats_final = dict()
proposed_number = 0
candidates = list()

location_commonscat_previous = ""


if proposeds is not None and len(proposeds) > 0:
    for proposed_cat in proposeds:
        print(proposed_cat)

        location_wd = modelwiki.get_wikidata_simplified(proposed_cat["location_wdid"])
        location_commonscat = location_wd.get("commons", "")
        if location_commonscat is None:
            location_commonscat = ""

        upper_location_wd = modelwiki.get_wikidata_simplified(
            proposed_cat["upper_location_wdid"]
        )
        location_upper_commonscat = upper_location_wd.get(
            "commons", " no commons name "
        )

        if location_upper_commonscat is None:
            print()
            print("go to next level")
            location_commonscat_previous = location_commonscat
            continue

        candidates.append(str(proposed_number))

        text = ""
        text += "{{Wikidata Infobox}}\n"
        text += "{{GeoGroup}}\n"
        text += (
            "[[Category:"
            + object_commonscat
            + " in "
            + str(location_upper_commonscat)
            + "]]\n"
        )
        if location_commonscat_previous != "" and location_commonscat == "":
            text += "[[Category:" + location_commonscat_previous + "]]\n"
        else:
            text += "[[Category:" + location_commonscat + "]]\n"

        proposed_cats_final[proposed_number] = dict()
        proposed_cats_final[proposed_number]["name"] = proposed_cat["name"]
        proposed_cats_final[proposed_number]["text"] = text

        print()
        print(proposed_number)
        print(proposed_cats_final[proposed_number]["name"])
        print(proposed_cats_final[proposed_number]["text"])
        print(
            "location_wdid="
            + proposed_cat.get("location_wdid", "")
            + ", it category is "
            + str(location_wd.get("commons", ""))
        )

        location_commonscat_previous = location_commonscat
        proposed_number = proposed_number + 1

    terminal_menu = TerminalMenu(
        candidates, title="Select number of proposed category for create"
    )
    menu_entry_index = terminal_menu.show()
    print(menu_entry_index)
    if menu_entry_index is None:
        quit()

    print("creating category")
    print(proposed_cats_final[menu_entry_index]["name"])
    print(proposed_cats_final[menu_entry_index]["text"])
    modelwiki.create_category(
        proposed_cats_final[menu_entry_index]["name"],
        proposed_cats_final[menu_entry_index]["text"],
    )
