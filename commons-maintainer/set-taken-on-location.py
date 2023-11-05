#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import logging
import subprocess
import os
import sys

sys.path.append('../commons-uploader')

from fileprocessor import Fileprocessor
from model_wiki import Model_wiki


fileprocessor = Fileprocessor()
modelwiki = Model_wiki()

categoryname = 'Shelepikha_(Moscow_Metro)'


location = 'Moscow'

modelwiki.category_add_template_taken_on(
    categoryname, location, dry_run=False, interactive=False)
