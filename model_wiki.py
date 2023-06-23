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
from simple_term_menu import TerminalMenu


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
    cache_category_object_in_location = dict()

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
        location = location.title()
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
        regex='(?i)date.*=.*\d\d\d\d-\d\d-\d\d.*\}\}'
        regex='(?i)Information[\S\s]*date[\S\s]*=[\S\s]*\d\d\d\d-\d\d-\d\d.*\}\}'
        gen1 = pagegenerators.CategorizedPageGenerator(category, recurse=True, start=None, total=None, content=True, namespaces=None)
        gen2 = pagegenerators.RegexBodyFilterPageGenerator(gen1,regex)
        regex
        gen2 = pagegenerators.RegexBodyFilterPageGenerator(gen1,regex)
        
        logging.getLogger().setLevel(logging.ERROR)
        logging.getLogger('foo').debug('bah')

        location = location.title()

        for page in gen:
            
            self.page_template_taken_on(page,location, dry_run, interactive,verbose=False)
        
    def page_template_taken_on(self, page, location, dry_run=True, interactive=False, verbose=True):
        assert page
        texts = dict()
        texts[0] = page.text
        
        if '.svg'.upper() in page.full_url().upper(): return False
        if '.tif'.upper() in page.full_url().upper(): return False
        if '.png'.upper() in page.full_url().upper(): return False
        if '.ogg'.upper() in page.full_url().upper(): return False


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
        
        

        
        datestr = self.get_date_from_pagetext(texts[1])
        if datestr == False:
            return False
        if '/' in datestr:
            raise ValueError('Slash symbols in date causes side-effects. Normalize date in '+page.full_url())
        if len(datestr) < len('yyyy-mm-dd'):
            return False
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
        self.difftext(texts[0],texts[2])        
        
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
    

    def take_user_wikidata_id(self, wdid) -> str:
        # parse user input wikidata string.
        # it may be wikidata id, wikidata uri, string.
        # call search if need
        # return valid wikidata id
        if Model_wiki.is_wikidata_id(wdid):
            result_wdid = wdid
        else:
            result_wdid = Model_wiki.search_wikidata_by_string(
                wdid, stop_on_error=True)

        return result_wdid
        
    @staticmethod
    def is_wikidata_id(text) -> bool:
        # check if string is valid wikidata id
        if text.startswith('Q') and text[1:].isnumeric():
            return True
        else:
            return False
            
    @staticmethod
    def search_wikidata_by_string(text, stop_on_error=True) -> str:
        warnings.warn('use wikidata_input2id', DeprecationWarning, stacklevel=2)
        cmd = ['wb', 'search', '--json', text]

        response = subprocess.run(cmd, capture_output=True)
        object_wd = json.loads(response.stdout.decode())
        if stop_on_error:
            if not len(object_wd) > 0:
                raise ValueError('not found in wikidata: '+text)

        return object_wd[0]['id']
        
    def wikidata_input2id(self,inp)->str:
        
        modelwiki = Model_wiki()
        
        #detect user input string for wikidata
        #if user print a query - search wikidata
        #returns wikidata id
        
        inp = self.prepare_wikidata_url(inp)
        if inp.startswith('Q'): return inp
        
        # search
        cmd = ['wb','search',inp,'--json','--lang','en']
        response = subprocess.run(cmd, capture_output=True)
        
        try:
            result_wd = json.loads(response.stdout.decode())
        except:
            self.logger.error('error parce json from wikibase query')
            self.logger.error(' '.join(cmd))
            self.logger.error(response.stdout.decode())
            
        candidates = list()
        for element in result_wd:
            candidates.append(element['id']+' '+element['display']['label']['value']+' '+element['display'].get('description',{'value':''})['value'])
        terminal_menu = TerminalMenu(candidates, title="Select street")
        menu_entry_index = terminal_menu.show()
        selected_url = result_wd[menu_entry_index]['id']
        print('For '+inp+' selected '+selected_url+' '+result_wd[menu_entry_index].get("description",'[no description]'))
        return selected_url

    def prepare_wikidata_url(self,wikidata)->str:
        # convert string https://www.wikidata.org/wiki/Q4412648 to Q4412648
        
        wikidata = str(wikidata).strip()
        wikidata = wikidata.replace('https://www.wikidata.org/wiki/','')
        if wikidata[0].isdigit() and not wikidata.upper().startswith('Q'):
            wikidata = 'Q'+wikidata
        return wikidata
        
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

    def input2list_wikidata(self,inp):

        if inp is None or inp == False: return list()
        if isinstance(inp,str):
            inp=([inp])
        secondary_wikidata_ids = list()
        for inp_wikidata in inp:
            wdid = self.wikidata_input2id(inp_wikidata)
            secondary_wikidata_ids.append(wdid)
        return secondary_wikidata_ids
        
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
            print('invalid date: '+text )
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

        if location in('Moscow', 'Saint Petersburg'):
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
        
    def get_wd_by_wdid(self,wdid)->dict:
        # if need python-only implementation: replace to pywikibot this
        
        cmd = ['wb', 'gt', '--json', '--no-minimize', wdid]
        response = subprocess.run(cmd, capture_output=True)
        object_wd = json.loads(response.stdout.decode())
        return object_wd
        
    def get_best_claim(self,wdid,prop)->str:
        assert prop.startswith('P')
        cmd = ['wb', 'claims', wdid, prop, '--json']
        response = subprocess.run(cmd, capture_output=True)
        object_wd = json.loads(response.stdout.decode())
        return object_wd[0]
    
    def get_upper_location_wdid(self,wdobj):
        if 'P131' in wdobj['claims']:
            return self.get_best_claim(wdobj['id'],'P131')
            #return self.get_wd_by_wdid(wdobj['claims']['P131'][0]['value'])
        
        return None
    def get_category_object_in_location(self,object_wdid,location_wdid,verbose=False)->str:
        cache_key = str(object_wdid)+'/'+location_wdid
        if cache_key in self.cache_category_object_in_location:
            return '[[Category:'+self.cache_category_object_in_location[cache_key]+']]'
        stop_hieraechy_walk = False
        cnt = 0
        geoobject_wd = self.get_wd_by_wdid(location_wdid)
        while not stop_hieraechy_walk:
            cnt=cnt+1
            if cnt > 6: stop_hieraechy_walk = True
            if verbose:
                print('search category for union '+str(object_wdid)+' '+str(geoobject_wd['id']))
            
            union_category_name = self.search_commonscat_by_2_wikidata(object_wdid,geoobject_wd['id'])
            if union_category_name is not None:
                print('found '+ '[[Category:'+union_category_name+']]')
                self.cache_category_object_in_location[cache_key]=union_category_name
                return '[[Category:'+union_category_name+']]'
            
            upper_wdid = self.get_upper_location_wdid(geoobject_wd)
            if upper_wdid is None: 
                stop_hieraechy_walk = True
                continue
            upper_wd = self.get_wd_by_wdid(upper_wdid)
            geoobject_wd = upper_wd
            
            
        return None
        
    def append_image_descripts_claim(self, commonsfilename, entity_list, dry_run):

        assert isinstance(entity_list, list)
        assert len(entity_list) > 0
        if dry_run:
            print('simulate add entities')
            self.pp.pprint(entity_list)
            return
        from fileprocessor import Fileprocessor
        fileprocessor = Fileprocessor()    
        commonsfilename = fileprocessor.prepare_commonsfilename(commonsfilename)

        site = pywikibot.Site("commons", "commons")
        site.login()
        site.get_tokens("csrf")  # preload csrf token
        page = pywikibot.Page(site, title=commonsfilename, ns=6)
        media_identifier = "M{}".format(page.pageid)

        # fetch exist structured data

        request = site.simple_request(
            action="wbgetentities", ids=media_identifier)
        raw = request.submit()
        existing_data = None
        if raw.get("entities").get(media_identifier).get("pageid"):
            existing_data = raw.get("entities").get(media_identifier)

        try:
            depicts = existing_data.get("statements").get("P180")
        except:
            depicts = None
        for entity in entity_list:
            if depicts is not None:
                # Q80151 (hat)
                if any(
                    statement["mainsnak"]["datavalue"]["value"]["id"] == entity
                    for statement in depicts
                ):
                    print(
                        "There already exists a statement claiming that this media depicts a "
                        + entity
                        + " continue to next entity"
                    )
                    continue

            statement_json = {
                "claims": [
                    {
                        "mainsnak": {
                            "snaktype": "value",
                            "property": "P180",
                            "datavalue": {
                                "type": "wikibase-entityid",
                                "value": {
                                    "numeric-id": entity.replace("Q", ""),
                                    "id": entity,
                                },
                            },
                        },
                        "type": "statement",
                        "rank": "normal",
                    }
                ]
            }

            csrf_token = site.tokens["csrf"]
            payload = {
                "action": "wbeditentity",
                "format": "json",
                "id": media_identifier,
                "data": json.dumps(statement_json, separators=(",", ":")),
                "token": csrf_token,
                "summary": "adding depicts statement",
                # in case you're using a bot account (which you should)
                "bot": False,
            }

            request = site.simple_request(**payload)
            try:
                request.submit()
            except pywikibot.data.api.APIError as e:
                print("Got an error from the API, the following request were made:")
                print(request)
                print("Error: {}".format(e))
                
                
                
    def search_commonscat_by_2_wikidata(self,abstract_wdid,geo_wdid):
    
        sample = """
                        SELECT DISTINCT ?item ?itemLabel WHERE {
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE]". }
  {
    SELECT DISTINCT ?item WHERE {
      ?item p:P971 ?statement0.
      ?statement0 (ps:P971) wd:Q22698.
      ?item p:P971 ?statement1.
      ?statement1 (ps:P971) wd:Q649.
    }
    LIMIT 100
  }
}

        """
        
        template = '''
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
        sparql = template
        sparql = sparql.replace('$SUBJECT', abstract_wdid)
        sparql = sparql.replace('$COUNTRY', geo_wdid)


        site = pywikibot.Site("wikidata", "wikidata")
        repo = site.data_repository()

        generator = pagegenerators.PreloadingEntityGenerator(pagegenerators.WikidataSPARQLPageGenerator(sparql,site=repo))
        for item in generator:
            item_dict = item.get()
            claim_list = item_dict["claims"].get('P373',())
            for claim in claim_list:
                commonscat = claim.getTarget()
                return commonscat
        return None

        
    def dev_search_wikidata_union_commons_cat(self, wikidata, country_wdid) -> str:
        # for given wikidata objects "PARK" and "COUNTRYNAME" finds CATEGORY:PARKS IN COUNTRYNAME usind P971. returns category name

        sample = '''

wb sparql t.sparql --format json
'''
        template = '''
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
        sparql = template
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

        return None
