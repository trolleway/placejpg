#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import pywikibot
import re, pprint, subprocess, json
from num2words import num2words
from transliterate import translit
import argparse
from simple_term_menu import TerminalMenu
import warnings


class CommonsOps:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger(__name__)
    pp = pprint.PrettyPrinter(indent=1)

    commonscat_instanceof_types = ("building", "street")

    

    def deprecated_create_commonscat_page(self, name, code) -> bool:
        # created with Bing Ai 2023-04-07
        # Import pywikibot library
        import pywikibot

        # Create a site object for wikimedia commons
        site = pywikibot.Site("commons", "commons")

        # Create a category object for the new category
        cat = pywikibot.Category(site, name)

        # Check if the category already exists
        if cat.exists():
            print("The category already exists.")
            return False
        else:
            # Create the category page with some text
            cat.text = code
            # Save the category page
            cat.save(
                "Creating new category"
            )
            self.logger.info("The category was created successfully. https://commons.wikimedia.org/wiki/"+name)
            return True

    def deprecated_create_building_category(self, wikidata, city_en, dry_mode=False ) -> str:
        if wikidata is None and dry_mode:
            print("commons category will be created here...")
            return

        assert wikidata.startswith("Q")
        
        cmd = ["wd", "generate-template", "--json",            '--no-minimize',  wikidata]
        response = subprocess.run(cmd, capture_output=True)
        building_dict_wd = json.loads(response.stdout.decode())

        assert "P669" in building_dict_wd["claims"], (
            "https://www.wikidata.org/wiki/"
            + wikidata
            + " must have P669 street name and housenumber"
        )
        # retrive category name for street
        cmd = [
            "wd",
            "generate-template",
            "--json",
            '--no-minimize',
            building_dict_wd["claims"]["P669"][0]["value"],
        ]

        response = subprocess.run(cmd, capture_output=True)
        street_dict_wd = json.loads(response.stdout.decode())
        housenumber = building_dict_wd["claims"]["P669"][0]['qualifiers']['P670'][0]["value"]
        if "P373" in  street_dict_wd["claims"]:
            category_street = street_dict_wd["claims"]["P373"][0]["value"]      
        else:
            category_street = str(street_dict_wd["sitelinks"]["commonswiki"])[9:]
        category_street +='|'+housenumber
               
        category_name = building_dict_wd["labels"]["en"]
        street_name_ru = street_dict_wd["labels"]["ru"]
        
        year = ""
        decade = ""
        year_field = None
        if "P1619" in building_dict_wd["claims"]:
            year_field = "P1619"
        elif "P580" in building_dict_wd["claims"]:
            year_field = "P580"
            year_field = "P1619"
        elif "P571" in building_dict_wd["claims"]:
            year_field = "P571"
        if year_field is not None:
            try:
                if building_dict_wd["claims"][year_field][0]["value"]["precision"] == 9:
                    year = building_dict_wd["claims"][year_field][0]["value"]["time"][0:4]
                if building_dict_wd["claims"][year_field][0]["value"]["precision"] == 8:
                    decade = (
                        building_dict_wd["claims"][year_field][0]["value"]["time"][0:3]
                        + "0"
                    )
            except:
                pass
            # no year in building
        assert isinstance(year, str)
        assert year == "" or len(year) == 4, "invalid year:" + str(year)
        assert decade == "" or len(decade) == 4, "invalid decade:" + str(decade)
        levels = 0
        try:
            levels = building_dict_wd["claims"]["P1101"][0]["value"]["amount"]
        except:
            pass
            # no levels in building
        assert isinstance(levels, int)
        assert levels == 0 or levels > 0, "invalid levels:" + str(levels)

        code = """
{{Object location}}
{{Wikidata infobox}}
{{Building address|Country=RU|City=%city%|Street name=%street%|House number=%housenumber%}}
[[Category:%building_function% in %city%]]
[[Category:%streetcategory%]]
"""

        if year != "":
            code += "[[Category:Built in %city% in %year%]]" + "\n"

        if decade != "":
            code += "[[Category:%decade%s architecture in %city%]]" + "\n"

        if levels > 0:
            code += "[[Category:%levelstr%-story buildings in %city%]]" + "\n"

        building_function='Buildings'
        if 'Q13402009' in building_dict_wd["claims"]["P31"]: building_function = 'Apartment buildings'
        if 'Q1021645' in building_dict_wd["claims"]["P31"]: building_function = 'Office buildings'
        
        
        code = code.replace("%building_function%", building_function)
        code = code.replace("%city%", city_en)
        #code = code.replace("%city_loc%", city_ru)
        code = code.replace("%streetcategory%", category_street)
        code = code.replace("%street%", street_name_ru)
        code = code.replace("%year%", year)
        code = code.replace("%housenumber%", housenumber)
        code = code.replace("%decade%", decade)
        if levels > 0 and levels < 21:
            code = code.replace("%levelstr%", str(num2words(levels).capitalize()))
        elif levels > 20:
            code = code.replace("%levelstr%", str(levels))

        if dry_mode:
            print()
            print(category_name)
            print(code)
            self.logger.info("dry mode, no creating wikidata entity")
            return

        commonscat_create_result = self.create_commonscat_page(
            name=category_name, code=code
        )

        # add to wikidata 2 links to commons category
        if commonscat_create_result:
            self.wikidata_add_commonscat(wikidata, category_name)

        return category_name
        

            
        
        
    def prepare_wikidata_url(self,wikidata)->str:
        # convert string https://www.wikidata.org/wiki/Q4412648 to Q4412648
        
        wikidata = str(wikidata).strip()
        wikidata = wikidata.replace('https://www.wikidata.org/wiki/','')
        if wikidata[0].isdigit() and not wikidata.upper().startswith('Q'):
            wikidata = 'Q'+wikidata
        return wikidata



    def deprecated_get_category_name_from_building(self, wikidata) -> str:
        assert wikidata.startswith("Q")
        cmd = ["wd", "generate-template", "--json", wikidata]
        response = subprocess.run(cmd, capture_output=True)
        building_dict_wd = json.loads(response.stdout.decode())
        category_name = building_dict_wd["labels"]["en"]
        return category_name



    


