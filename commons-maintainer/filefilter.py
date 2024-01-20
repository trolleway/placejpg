#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os, subprocess, logging, argparse, sys

import pywikibot
from pywikibot import pagegenerators
from pywikibot import exceptions
from datetime import datetime
from dateutil import parser
from urllib.parse import urlparse
from exif import Image


class Filtrator:
    cachedir='maintainer_cache'

    def get_exif_from_file(self,path):
        try:
            with open(path, "rb") as image_file:
                image_exif = Image(image_file)
                return image_exif
        except:
            return None
    def image2datetime(self, path):
    
        def get_datetime_from_string(s):
            # find the substring that matches the format YYYYMMDD_HHMMSS
            # assume it is always 15 characters long and starts with a digit

            for i in range(len(s) - 15):
                if s[i].isdigit():
                    date_str = s[i:i+15]
                    print('test '+date_str)
                    try:
                        datetime.strptime(date_str, "%Y%m%d_%H%M%S")
                        # Valid date string
                        break
                    except ValueError:
                        pass
                        #go next char
                    
            # use datetime.strptime() to convert the substring to a datetime object
            date_obj = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
            return date_obj

        with open(path, "rb") as image_file:
            if not path.lower().endswith('.stl'):
                try:
                    image_exif = Image(image_file)
                    
                    dt_str = image_exif.get("datetime_original", None)

                    dt_obj = datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
                except:
                    dt_obj = None
                    cmd = [self.exiftool_path, path, "-datetimeoriginal", "-csv"]
                    if path.lower().endswith('.mp4'):
                        cmd = [self.exiftool_path, path, "-createdate", "-csv"]
                        self.logger.debug('video')

                    exiftool_text_result = subprocess.check_output(cmd)
                    tmp = exiftool_text_result.splitlines()[1].split(b",")
                    if len(tmp) > 1:
                        dt_str = tmp[1]
                        dt_obj = datetime.strptime(
                            dt_str.decode("UTF-8"), "%Y:%m:%d %H:%M:%S"
                        )
            elif path.lower().endswith('.stl'):
                dt_obj = None

            if dt_obj is None:
                dt_obj = get_datetime_from_string(os.path.basename(path))
                
               
                #except:
                #    print(f'file {path}: failed to get date, failed to read from start of filename')
                #    quit()

            if dt_obj is None:
                return None
            return dt_obj
        
        
        
    def get_date_from_pagetext(self,test_str) -> str:
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
        
    def dowload_or_cache_read(self,FilePage)->str:
        if not os.path.isdir(self.cachedir):
            os.makedirs(self.cachedir)
            
        url = FilePage.get_file_url()   
        filepath = os.path.join(self.cachedir, os.path.basename(urlparse(url).path) )
        if os.path.isfile(filepath):
            return filepath
        FilePage.download(filename=filepath)
        return filepath
        
    def get_ts_exif_from_page(self,page)->str:
        """
        for FilePage object download/read from cache file, and read timestamp from exif
        """    
        local_filepath = self.dowload_or_cache_read(page)
        dt_obj = self.image2datetime(local_filepath)
        return dt_obj
        
    def get_exif_from_page(self,page)->str:
        """
        for FilePage object download/read from cache file, and read timestamp from exif
        """    
        local_filepath = self.dowload_or_cache_read(page)
        exif = self.get_exif_from_file(local_filepath)
        return exif        
        
    def print_cat(self,categoryname):
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
            #datetext = self.get_date_from_pagetext(page.text)
            
            ts = page.latest_file_info.timestamp
            #ts_exif=self.get_ts_exif_from_page(page)
            exif = self.get_exif_from_page(page)
            print(page.title(),page.pageid,exif.get('datetime_original',''),exif.get('model',''))
            #CATEGORIES TEXT
            c=''
            categories=list()
            for line in page.text.splitlines():
                if line.strip().startswith('[[Category:'):
                    if not any(substring in line.strip() for substring in ['ISO','Uploaded','F-number','Lens','Panoramio files uploaded by Panoramio upload bot']):
                        c=line.strip().replace('[[Category:','')
                        categories.append(c)
            files.append({'name':page.title(),'id':page.pageid,'categories':categories,'thumbnail':page.get_file_url(450,300), 'exif':exif})

        html="""<html>
        <head>
        </head>
        <body>
        <table>
        """
        files = sorted(files, key=lambda x: x.get('exif',0).get('datetime_original',0), reverse=False)
        for fi in files:
            html+='''<tr><td><img src="{thumb}"></td><td>_replace{id}</td><td>{categories}</td><td>{ts}<br>{model}</td></tr>'''.format(thumb=fi['thumbnail'],
                                                                                                                    id=fi['id'],
                                                                                                                    categories='</br>'.join(fi['categories']),
                                                                                                                    ts=fi['exif'].get('datetime_original',''),
                                                                                                                    model = fi['exif'].get('model','')
                                                                                                                    )+"\n"

        html+='</table></html>'
        with open("table.html", "w") as file:
            file.write(html)



    

#parser = argparse.ArgumentParser()
#parser.add_argument('--category', type=str, required=False)
#args = parser.parse_args()

processor = Filtrator()
processor.print_cat('Moscow photographs taken on 2016-02-13')

