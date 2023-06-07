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
import wikitextparser as wtp


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

    def wikipedia_get_page_content(self, page) -> str:

        # check cache
        import sys
        pagename = page.title()
        if pagename in self.wiki_content_cache:
            return self.wiki_content_cache[pagename]

        pagecode = page.text
        self.wiki_content_cache[pagename] = pagecode
        assert sys.getsizeof(pagecode) > 25

        return pagecode

    def is_change_need(self, pagecode, operation) -> bool:
        operations = ('taken on', 'taken on location')
        assert operation in operations

        if operation == 'taken on':
            if '{{Taken on'.upper() in pagecode.upper():
                return False
            else:
                return True

        return False

    def page_name_canonical(self, pagecode) -> str:
        # [[commons:File:Podolsk, Moscow Oblast, Russia - panoramio (152).jpg]]
        # File:Podolsk, Moscow Oblast, Russia - panoramio (152).jpg

        pagecode = str(pagecode)
        pagecode = pagecode.replace('https://commons.wikimedia.org/wiki/', '')
        pagecode = pagecode.replace('[[commons:', '').replace(']]', '')
        return pagecode

    def op1(self):

        pages = self.search_files_geo(lat=55.42, lon=37.52)

        for page in pages:
            print(page.title())
            pagecode = self.wikipedia_get_page_content(page)
            if self.is_change_need(pagecode, 'taken on'):
                print('---need change')
                
    def url_add_template_taken_on(self, pagename,location, dry_run=True):
        assert pagename
        location = location.capitalize()
        site = pywikibot.Site("commons", "commons")
        site.login()
        site.get_tokens("csrf")  # preload csrf token
        pagename = self.page_name_canonical(pagename)
        page = pywikibot.Page(site, title=pagename)
        
        self.page_template_taken_on(page,location, dry_run)
                        
    def category_add_template_taken_on(self, categoryname ,location, dry_run=True,interactive=False):
        assert categoryname
        site = pywikibot.Site("commons", "commons")
        site.login()
        site.get_tokens("csrf")  # preload csrf token
        category = pywikibot.Category(site, categoryname)
        gen = pagegenerators.CategorizedPageGenerator(category, recurse=True, start=None, total=None, content=True, namespaces=None)
        
        logging.getLogger().setLevel(logging.ERROR)
        logging.getLogger('foo').debug('bah')

        location = location.capitalize()
        #assert len(pages)>0, len(pages)
        for page in gen:
            self.page_template_taken_on(page,location, dry_run, interactive,verbose=False)
        
    def page_template_taken_on(self, page, location, dry_run=True, interactive=False, verbose=True):
        assert page
        texts = dict()
        texts[0] = page.text


        if '{{Information'.upper() not in texts[0].upper():
            self.logger.debug('template Information not exists in '+page.title())
            return False
        if '|location='.upper()+location.upper() in texts[0].upper():
            self.logger.debug('|location='+location+' already in page')
            return False
        try:
            texts[1] = self._text_add_template_taken_on(texts[0])
        except:
            raise ValueError('invalid page text in ' +page.full_url())
        assert 'Taken on'.upper() in texts[1].upper() or 'According to Exif data'.upper() in texts[1].upper(), 'wrong text in '+page.title()
        
        self.difftext(texts[0],texts[1])

        
        datestr = self.get_date_from_pagetext(texts[1])
        if datestr == False:
            return False
        if '/' in datestr:
            raise ValueError('Slash symbols in date causes side-effects. Normalize date in '+page.full_url())
        assert datestr, 'invalid date parce in '+page.full_url()
        print('will create category '+location+' on '+datestr)
        
        location_value_has_already = self._text_get_template_taken_on_location(texts[1])
        
        if location_value_has_already is None:
            texts[2] = self._text_add_template_taken_on_location(texts[1], location)
        else:
            texts[2] = self._text_get_template_replace_on_location(texts[1], location)
            
        if texts[2] == False:
            return False
        if '|location='+location+'}}' not in texts[2]: return False
        self.difftext(texts[1],texts[2])        
        
        if verbose:
            print('----------- proposed page content ----------- '+datestr+ '--------')
           
            print(texts[2])
        if not dry_run and not interactive:
            page.text = texts[2]
            page.save('add {{Taken on location}} template')
            self.create_category_taken_on_day(location,datestr)
            
        if interactive:
            answer = input(" do change on  "+page.full_url() + "\n y / n   ? ")
            # Remove white spaces after the answers and convert the characters into lower cases.
            answer = answer.strip().lower()
         
            if answer in ["yes", "y", "1"]:
                page.text = texts[2]
                page.save('add {{Taken on location}} template')
                self.create_category_taken_on_day(location,datestr)



    def difftext(self,text1,text2):
        l = 0
        is_triggered = 0
        for l in range(0, len(text1.splitlines())):
            if text1.splitlines()[l] != text2.splitlines()[l]:
                is_triggered += 1
                if is_triggered==1: print('text changed:')
                print(text1.splitlines()[l])
                print(text2.splitlines()[l])
                print('^^^^^')
                
    def _text_get_template_replace_on_location(self,test_str,location):
        import re
        
        regex = r"^.*(?:Information|photograph)[\s\S]*?Date\s*?=.*location=(?P<datecontent>[\s\S]*?)[\|\}}\n].*$"
        
        
        matches = re.finditer(regex, test_str, re.UNICODE | re.MULTILINE | re.IGNORECASE)

        for matchNum, match in enumerate(matches, start=1):
            

            
            for groupNum in range(0, len(match.groups())):
                groupNum = groupNum + 1
                
                groupstart = match.start(groupNum)
                groupend = match.end(groupNum)
                content =  match.group(groupNum)
                

        
        text = test_str[0:groupstart] +location+test_str[groupend:]
        return text
            
            
    def _text_get_template_taken_on_location(self,test_str):
        # return content of "location" if exists
        
        import re

        regex = r"^.*(?:Information|photograph)[\s\S]*?Date\s*?=.*location=(?P<datecontent>[\s\S]*?)[\|\}}\n].*$"

        matches = re.search(regex, test_str, re.IGNORECASE | re.UNICODE | re.MULTILINE)

        if matches:

            
            for groupNum in range(0, len(matches.groups())):
                groupNum = groupNum + 1
                

                return(matches.group(groupNum))
    
    def is_taken_on_in_text(self,test_str):
        import re

        regex = r"^.*(?:Information|photograph)[\s\S]*?Date\s*?=.*?(taken on|According to Exif data)\s*?[\|\n].*$"


        matches = re.search(regex, test_str, re.IGNORECASE | re.UNICODE | re.MULTILINE)

        if matches:

            
            for groupNum in range(0, len(matches.groups())):
                groupNum = groupNum + 1
                
  
                

                
                if matches.group(groupNum) is not None: return True
        return False

    def _text_add_template_taken_on(self,test_str):
        assert test_str 

        if self._text_get_template_taken_on_location(test_str) is not None: return test_str  
        if self.is_taken_on_in_text(test_str): return test_str
        # test_str name comes from onine regex editor
        import re
        
        regex = r"^.*(?:Information|photograph)[\s\S]*?Date\s*?=(?P<datecontent>[\s\S]*?)[\|\n].*$"
        
        
        matches = re.finditer(regex, test_str, re.UNICODE | re.MULTILINE | re.IGNORECASE)
        


        for matchNum, match in enumerate(matches, start=1):
            

            
            for groupNum in range(0, len(match.groups())):
                groupNum = groupNum + 1
                
                groupstart = match.start(groupNum)
                groupend = match.end(groupNum)
                content =  match.group(groupNum)
                

        
        text = test_str[0:groupstart] + ' {{Taken on|'+content.strip()+"}}"+test_str[groupend:]
        return text

            
    def _text_add_template_taken_on_location(self,test_str, location):

        if '|location'.upper() in test_str.upper():
            return False
        # test_str name comes from onine regex editor
        import re
        
        regex = r"^.*(?:Information|photograph)[\s\S]*Date\s*=\s*{{(?:Taken on|According to Exif data)\s*\|[\s\S]*?(?P<taken_on_end>)}}.*$"
        
        
        matches = re.finditer(regex, test_str, re.MULTILINE | re.IGNORECASE)

        for matchNum, match in enumerate(matches, start=1):
            

            
            for groupNum in range(0, len(match.groups())):
                groupNum = groupNum + 1
                
                groupstart = match.start(groupNum)
                groupend = match.end(groupNum)
                content =  match.group(groupNum)
                

        
        text = test_str[0:groupstart] + '|location='+location+""+test_str[groupend:]
        return text

    def get_date_from_pagetext(self,test_str)->str:
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
                content =  match.group(groupNum)
                
        
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

    def create_category_taken_on_day(self, location, yyyymmdd):
        if len(yyyymmdd) != 10:
            return False

        categoryname = '{location}_photographs_taken_on_{yyyymmdd}'.format(
            location=location, yyyymmdd=yyyymmdd)

        pagename = 'Category:'+categoryname
        if not self.is_category_exists(pagename):

            self.logger.info('create page '+pagename)
            if location == 'Moscow':
                content = '{{Moscow photographs taken on navbox}}'
            else:
                content = '{{'+location+' photographs taken on navbox|' + \
                    yyyymmdd[0:4]+'|'+yyyymmdd[5:7]+'|'+yyyymmdd[8:10]+'}}'
            self.create_page(pagename, content, 'create category')

        else:
            self.logger.info('page alreaty exists '+pagename)

        if location == 'Moscow':
            self.create_category_taken_on_day('Russia', yyyymmdd)

    def is_category_exists(self, categoryname):

        site = pywikibot.Site("commons", "commons")
        site.login()
        site.get_tokens("csrf")  # preload csrf token
        page = pywikibot.Page(site, title=categoryname)
        return page.exists()

    def create_page(self, title, content, savemessage):
        site = pywikibot.Site("commons", "commons")
        site.login()
        site.get_tokens("csrf")  # preload csrf token
        page = pywikibot.Page(site, title=title)
        page.text = content
        page.save(savemessage)

        return True

    def search_files_geo(self, lat, lon):
        site = pywikibot.Site("commons", "commons")
        pages = pagegenerators.SearchPageGenerator('Svetlov Artem filetype:bitmap nearcoord:2km,{lat},{lon}'.format(
            lat=lat, lon=lon), total=8, namespaces=None, site=site)

        return pages

    def search_category_by_wikidata_union(self, wikidata, country_wdid) -> str:
        # for given wikidata objects "PARK" and "COUNTRYNAME" finds CATEGORY:PARKS IN COUNTRYNAME usind P971

        sample = '''
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
        sparql = sparql.replace('$SUBJECT', wikidata)
        sparql = sparql.replace('$COUNTRY', country_wdid)

        tempfile_sparql = tempfile.NamedTemporaryFile()

        # Open the file for writing.
        with open(tempfile_sparql.name, 'w') as f:
            # with open('temp.rq', 'w') as f:
            # where `stuff` is, y'know... stuff to write (a string)
            f.write(sparql)

        cmd = ['wb', 'sparql', tempfile_sparql.name, '--format', 'json']

        response = subprocess.run(cmd, capture_output=True)

        dict_wd = json.loads(response.stdout.decode())
        try:
            wikidata_id = dict_wd[0]['item']
            return wikidata_id
        except:
            return None

        return ''
