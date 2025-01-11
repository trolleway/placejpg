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

    

   
            
        
        
    def prepare_wikidata_url(self,wikidata)->str:
        # convert string https://www.wikidata.org/wiki/Q4412648 to Q4412648
        
        wikidata = str(wikidata).strip()
        wikidata = wikidata.replace('https://www.wikidata.org/wiki/','')
        if wikidata[0].isdigit() and not wikidata.upper().startswith('Q'):
            wikidata = 'Q'+wikidata
        return wikidata




    


