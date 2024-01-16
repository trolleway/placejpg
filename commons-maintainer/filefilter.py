#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os, subprocess, logging, argparse, sys

import pywikibot
from pywikibot import pagegenerators
from pywikibot import exceptions
from datetime import datetime
from dateutil import parser

def get_date_from_pagetext(test_str) -> str:
    content = ''
    # test_str name comes from onine regex editor
    import re

    regex = r"^.*?(?:Information|photograph)[\s\S]*?Date\s*=\s*{{(?:Taken on|According to Exif data)\s*\|(?P<datecontent>[\s\S]*?)(?:}}|\|).*$"

    matches = re.finditer(regex, test_str, re.MULTILINE | re.IGNORECASE)

    for matchNum, match in enumerate(matches, start=1):

        for groupNum in range(0, len(match.groups())):
            groupNum = groupNum + 1

            groupstart = match.start(groupNum)
            groupend = match.end(groupNum)
            content = match.group(groupNum)

    if content == '':
        print("not found date in \n"+test_str)
        return False
    text = content.strip()
    text = text[:10]
    try:
        parser.parse(text)
    except:
        print('invalid date: '+text)
        return False
    return text
    
    
def print_cat(categoryname):
    assert categoryname
    total_files = 0
    site = pywikibot.Site("commons", "commons")
    site.login()
    site.get_tokens("csrf")  # preload csrf token
    category = pywikibot.Category(site, categoryname)
    
    gen1 = pagegenerators.CategorizedPageGenerator(
        category, recurse=False, start=None, total=None, content=True, namespaces=None)
    #gen2 = pagegenerators.PageTitleFilterPageGenerator(gen1,ignore_list=['Panoramio'])
    files=list()
    for page in gen1:
        if 'anoramio' not in page.title():
            continue
        if '{{Duplicate' in page.text:
            continue
        
        #page.get_file_url(300,200)
        total_files = total_files+1
        #datetext = get_date_from_pagetext(page.text)
        print(page.title(),page.pageid,page.latest_file_info.timestamp)
        ts = page.latest_file_info.timestamp
        #CATEGORIES TEXT
        c=''
        categories=list()
        for line in page.text.splitlines():
            if line.strip().startswith('[[Category:'):
                if not any(substring in line.strip() for substring in ['ISO','Uploaded','F-number','Lens']):
                    c=line.strip().replace('[[Category:','')
                    categories.append(c)
        files.append({'name':page.title(),'id':page.pageid,'categories':categories,'thumbnail':page.get_file_url(450,300), 'ts':ts})

    html="""<html>
    <head>
    </head>
    <body>
    <table>
    """
    files = sorted(files, key=lambda x: x.get('ts',0), reverse=False)
    for fi in files:
        html+='''<tr><td><img src="{thumb}"></td><td>{id}</td><td>{categories}</td><td>{ts}</td></tr>'''.format(thumb=fi['thumbnail'],
                                                                                                                id=fi['id'],
                                                                                                                categories='</br>'.join(fi['categories']),
                                                                                                                ts=fi.get('ts',''))+"\n"

    html+='</table></html>'
    with open("table.html", "w") as file:
        file.write(html)



   

#parser = argparse.ArgumentParser()
#parser.add_argument('--category', type=str, required=False)
#args = parser.parse_args()

print_cat('Saint_Petersburg_photographs_taken_on_2011-04-02')

