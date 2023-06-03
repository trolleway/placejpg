import pywikibot
import json

from exif import Image
import exiftool
import locale

from datetime import datetime
from dateutil import parser
import os
import logging
import pprint
import subprocess
from transliterate import translit
from pywikibot.specialbots import UploadRobot
from pywikibot import pagegenerators
import urllib


# TODO: Rename to model_pywikibot

from fileprocessor import Fileprocessor

class Model_wiki:
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger(__name__)
    pp = pprint.PrettyPrinter(indent=4)



    
    wiki_content_cache = dict()
    
    def wikipedia_get_page_content(self,page)-> str: 
    
        #check cache
        import sys
        pagename = page.title()
        if pagename in self.wiki_content_cache :
            return self.wiki_content_cache[pagename]

        pagecode=page.text
        self.wiki_content_cache[pagename] = pagecode
        assert sys.getsizeof(pagecode) > 25

        return pagecode

    def is_change_need(self,pagecode,operation)->bool:
        operations = ('taken on','taken on location')
        assert operation in operations
        
        if operation == 'taken on':
            if '{{Taken on'.upper() in pagecode.upper():
                return False
            else:
                return True
        
        return False
            
            
    def page_name_canonical(self,pagecode)->str:
        # [[commons:File:Podolsk, Moscow Oblast, Russia - panoramio (152).jpg]]
        # File:Podolsk, Moscow Oblast, Russia - panoramio (152).jpg
        
        pagecode = str(pagecode)
        pagecode = pagecode.replace('[[commons:','').replace(']]','')
        return pagecode
        
        
    def op1(self):
        
        pages = self.search_files_geo(lat=55.42,lon=37.52)
        
        for page in pages:
            print(page.title())
            pagecode = self.wikipedia_get_page_content(page)
            if self.is_change_need(pagecode,'taken on'):
                print('---need change')
            
    def create_category_taken_on_day(self,location,yyyymmdd):
        assert len(yyyymmdd)==10
        
        categoryname = '{location}_photographs_taken_on_{yyyymmdd}'.format(location=location,yyyymmdd=yyyymmdd)
        
        pagename = 'Category:'+categoryname
        if not self.is_category_exists(pagename):
            
            self.logger.info('create page '+pagename)
            if location == 'Moscow':
                content = '{{Moscow photographs taken on navbox}}'
            else:
                content = '{{'+location+' photographs taken on navbox|'+yyyymmdd[0:4]+'|'+yyyymmdd[5:7]+'|'+yyyymmdd[8:10]+'}}'
            self.create_page(pagename,content,'create category')

        else:
            self.logger.info('page alreaty exists '+pagename)
            
        if location=='Moscow':
            self.create_category_taken_on_day('Russia',yyyymmdd)
    
    def is_category_exists(self,categoryname):
        
        site = pywikibot.Site("commons", "commons")
        site.login()
        site.get_tokens("csrf")  # preload csrf token
        page = pywikibot.Page(site, title=categoryname)
        return page.exists()
    
    def create_page(self,title,content,savemessage):
        site = pywikibot.Site("commons", "commons")
        site.login()
        site.get_tokens("csrf")  # preload csrf token
        page = pywikibot.Page(site, title=title)
        page.text = content
        page.save(savemessage)
        
        return True
        
    def search_files_geo(self,lat,lon):
        site = pywikibot.Site("commons", "commons")
        pages = pagegenerators.SearchPageGenerator('Svetlov Artem filetype:bitmap nearcoord:2km,{lat},{lon}'.format(lat=lat,lon=lon), total=8, namespaces=None, site=site)

        return pages
    

   
        




    def search_category_by_wikidata_union(self, wikidata, country_wdid) -> str:
        # for given wikidata objects "PARK" and "COUNTRYNAME" finds CATEGORY:PARKS IN COUNTRYNAME usind P971

        sample='''
        SELECT DISTINCT ?item ?itemLabel WHERE {
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE]". }
  {
    SELECT DISTINCT ?item WHERE {
      ?item p:P971 ?statement0.
      ?statement0 (ps:P971) wd:$SUBJECT.
      ?item p:P971 ?statement1.
      ?statement1 (ps:P971) wd:$COUNTRY.
    }
    LIMIT 100
  }
}
'''
        sparql = sample
        sparql = sparql.replace('$SUBJECT',wikidata)
        sparql = sparql.replace('$COUNTRY',country_wdid)

        tempfile_sparql = tempfile.NamedTemporaryFile()

        # Open the file for writing.
        with open(tempfile_sparql.name, 'w') as f:
        #with open('temp.rq', 'w') as f:
            f.write(sparql) # where `stuff` is, y'know... stuff to write (a string)
      
        cmd = ['wb', 'sparql', tempfile_sparql.name, '--format', 'json']
        
        response = subprocess.run(cmd, capture_output=True)

        dict_wd = json.loads(response.stdout.decode())
        try:
            wikidata_id = dict_wd[0]['item']
            return wikidata_id
        except:
            return None
        
        
        return ''
