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


v = modelwiki.get_settlement_for_object('Q4216574',verbose=True) 
assert v== 'Q649'
v = modelwiki.get_settlement_for_object('Q4216577',verbose=True) 
assert v == 'Q656'
