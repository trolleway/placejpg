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

categoryname = 'Photographs_by_Artem_Svetlov/Moscow_Oblast'


location = 'Moscow Oblast'

modelwiki.category_add_template_taken_on(
    categoryname, location, dry_run=False, interactive=False)
