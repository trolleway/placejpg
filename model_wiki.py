import pywikibot
import json

from exif import Image
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
from pywikibot import exceptions

import urllib
import wikitextparser as wtp
from simple_term_menu import TerminalMenu
import pickle
import re
import traceback
from tqdm import tqdm


from fileprocessor import Fileprocessor


class Model_wiki:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger(__name__)
    pp = pprint.PrettyPrinter(indent=4)

    wiki_content_cache = dict()
    cache_category_object_in_location = dict()
    wikidata_cache = dict()
    wikidata_cache_filename = 'temp_wikidata_cache.dat'
    optional_langs = ('de', 'fr', 'it', 'es', 'pt', 'uk', 'be', 'ja')

    def __init__(self):
        if not os.path.isfile('user-config.py'):
            raise Exception('''Now you should enter Wikimedia user data in config. Call \n cp user-config.example.py user-config.py
        \n open user-config.py in text editor, input username,  and run this script next time''')

        self.wikidata_cache = self.wikidata_cache_load(
            wikidata_cache_filename=self.wikidata_cache_filename)

    def replace_file_commons(self, pagename, filepath):
        assert pagename
        # Login to your account
        site = pywikibot.Site('commons', 'commons')
        site.login()
        site.get_tokens("csrf")  # preload csrf token

        # Replace the file
        file_page = pywikibot.FilePage(site, pagename)

        file_page.upload(file=filepath, comment='Replacing file')

        return

    def wikidata_cache_load(self, wikidata_cache_filename):
        if os.path.isfile(wikidata_cache_filename) == False:
            cache = {'entities_simplified': {},  'commonscat_by_2_wikidata': {}, 'commonscat_exists_set': set()}
            return cache
        else:
            file = open(wikidata_cache_filename, 'rb')

            # dump information to that file
            cache = pickle.load(file)

            # close the file
            file.close()
            return cache

    def wikidata_cache_save(self, cache, wikidata_cache_filename) -> bool:
        file = open(wikidata_cache_filename, 'wb')

        # dump information to that file
        pickle.dump(cache, file)

        # close the file
        file.close()

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

    def url_add_template_taken_on(self, pagename, location, dry_run=True):
        assert pagename
        location = location.title()
        site = pywikibot.Site("commons", "commons")
        site.login()
        site.get_tokens("csrf")  # preload csrf token
        pagename = self.page_name_canonical(pagename)
        page = pywikibot.Page(site, title=pagename)

        self.page_template_taken_on(page, location, dry_run)

    def category_add_template_taken_on(self, categoryname, location, dry_run=True, interactive=False):
        assert categoryname
        total_files = 0
        site = pywikibot.Site("commons", "commons")
        site.login()
        site.get_tokens("csrf")  # preload csrf token
        category = pywikibot.Category(site, categoryname)
        regex = '(?i)date.*=.*\d\d\d\d-\d\d-\d\d.*\}\}'
        regex = '(?i)Information[\S\s]*date[\S\s]*=[\S\s]*\d\d\d\d-\d\d-\d\d.*\}\}'
        gen1 = pagegenerators.CategorizedPageGenerator(
            category, recurse=False, start=None, total=None, content=True, namespaces=None)
        gen2 = pagegenerators.RegexBodyFilterPageGenerator(gen1, regex)
        regex
        gen2 = pagegenerators.RegexBodyFilterPageGenerator(gen1, regex)
        for page in gen2:
            print(page)
            total_files = total_files+1

        del gen1
        del gen2
        gen1 = pagegenerators.CategorizedPageGenerator(
            category, recurse=False, start=None, total=None, content=True, namespaces=None)
        gen2 = pagegenerators.RegexBodyFilterPageGenerator(gen1, regex)

        gen2 = pagegenerators.RegexBodyFilterPageGenerator(gen1, regex)

        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger('foo').debug('bah')

        location = location.title()
        pbar = tqdm(total=total_files)
        for page in gen2:

            self.page_template_taken_on(
                page, location, dry_run, interactive, verbose=False)
            pbar.update(1)
        pbar.close()

    def location_string_parse(self, text) -> tuple:
        if text is None:
            return None, None
        text = text.strip()
        if text is None or text == "":
            return None, None
        struct = re.split(" |,|\t|\|", text)
        if len(struct) < 2:
            return None, None
        return float(struct[0]), float(struct[-1])

    def create_wikidata_building(self, data, dry_mode=False):
        assert "street_wikidata" in data

        # get street data from wikidata
        assert data["street_wikidata"] is not None
        cmd = ["wd", "generate-template", "--json", data["street_wikidata"]]
        response = subprocess.run(cmd, capture_output=True)
        street_dict_wd = json.loads(response.stdout.decode())
        data["street_name_ru"] = street_dict_wd["labels"]["ru"]
        data["street_name_en"] = street_dict_wd["labels"]["en"]

        wikidata_template = """
    {
      "type": "item",
      "labels": {
        "ru": ""
      },
      "descriptions": {
        "ru": ""
      },
      "aliases": {},
      "claims": {
        "P31": ["Q41176"],
        "P17": "Q159",
        "P625":{ 
            "value":{
          "latitude": 55.666,
          "longitude": 37.666,
          "precision": 0.0001,
          "globe": "http://www.wikidata.org/entity/Q2"
            }
        }
      }
    }
    """

        data["lat"], data["lon"] = self.location_string_parse(
            data["latlonstr"])

        assert data["lat"] is not None
        assert data["lon"] is not None
        assert data["street_name_ru"] is not None
        assert data["street_name_en"] is not None
        assert data["housenumber"] is not None
        assert data["street_wikidata"] is not None
        wd_object = json.loads(wikidata_template)
        wd_object["labels"]["ru"] = data["street_name_ru"] + \
            " " + data["housenumber"]
        wd_object["labels"]["en"] = (
            data["city"] + ' '
            + data["street_name_en"]
            + " "
            + translit(data["housenumber"], "ru", reversed=True)
        )
        wd_object["descriptions"]["ru"] = "Здание в " + data["city"]
        wd_object["descriptions"]["en"] = "Building in " + data["city"]
        wd_object["aliases"] = {"ru": list()}
        wd_object["aliases"]["ru"].append(
            data["city"] + ' ' + data["street_name_ru"] +
            " дом " + data["housenumber"]
        )
        wd_object["claims"]["P625"]["value"]["latitude"] = round(
            float(data["lat"]), 5
        )  # coords
        wd_object["claims"]["P625"]["value"]["longitude"] = round(
            float(data["lon"]), 5
        )  # coords
        if data.get("coord_source", None) is not None and data["coord_source"].lower() == "yandex maps":
            wd_object["claims"]["P625"]["references"] = list()
            wd_object["claims"]["P625"]["references"].append(dict())
            wd_object["claims"]["P625"]["references"][0]["P248"] = "Q4537980"
        if data.get("coord_source", None) is not None and data["coord_source"].lower() == "osm":
            wd_object["claims"]["P625"]["references"] = list()
            wd_object["claims"]["P625"]["references"].append(dict())
            wd_object["claims"]["P625"]["references"][0]["P248"] = "Q936"
        if data.get("coord_source", None) is not None and data["coord_source"].lower() == "reforma":
            wd_object["claims"]["P625"]["references"] = list()
            wd_object["claims"]["P625"]["references"].append(dict())
            wd_object["claims"]["P625"]["references"][0]["P248"] = "Q117323686"
        wd_object["claims"]["P669"] = {
            "value": data["street_wikidata"],
            "qualifiers": {"P670": data["housenumber"]},
        }

        if "year" in data:
            wd_object["claims"]["P1619"] = {
                "value": {"time": str(data["year"])}}
            if "year_source" or "year_url" in data:
                wd_object["claims"]["P1619"]["references"] = list()
                wd_object["claims"]["P1619"]["references"].append(dict())
                if data.get("year_source") == "2gis":
                    wd_object["claims"]["P1619"]["references"][0]["P248"] = "Q112119515"
                if data.get("year_source") == "wikimapia":
                    wd_object["claims"]["P1619"]["references"][0]["P248"] = "Q187491"
                if 'https://2gis.ru' in data.get('year_url', ''):
                    wd_object["claims"]["P1619"]["references"][0]["P248"] = "Q112119515"
                if 'reformagkh.ru' in data.get('year_url', ''):
                    wd_object["claims"]["P1619"]["references"][0]["P248"] = "Q117323686"

                if "year_url" in data:
                    wd_object["claims"]["P1619"]["references"][0]["P854"] = data[
                        "year_url"
                    ]

        if "levels" in data:
            wd_object["claims"]["P1101"] = {
                "value": {"amount": int(data["levels"]), "unit": "1"}
            }
            if "levels_source" or "levels_url" in data:
                wd_object["claims"]["P1101"]["references"] = list()
                wd_object["claims"]["P1101"]["references"].append(dict())
                if data.get("levels_source") == "2gis":
                    wd_object["claims"]["P1101"]["references"][0]["P248"] = "Q112119515"
                if data.get("levels_source") == "wikimapia":
                    wd_object["claims"]["P1101"]["references"][0]["P248"] = "Q187491"
                if 'https://2gis.ru' in data.get('levels_url', ''):
                    wd_object["claims"]["P1101"]["references"][0]["P248"] = "Q112119515"
                if 'reformagkh.ru' in data.get('levels_url', ''):
                    wd_object["claims"]["P1101"]["references"][0]["P248"] = "Q117323686"

            if "levels_url" in data:
                wd_object["claims"]["P1101"]["references"][0]["P854"] = data["levels_url"]
        if 'building' in data and data['building'] == 'apartments':
            wd_object["claims"]["P31"] = 'Q13402009'
        if 'building' in data and data['building'] in ('commercial', 'office'):
            wd_object["claims"]["P31"] = 'Q1021645'

        with open("temp_json_data.json", "w") as outfile:
            json.dump(wd_object, outfile)
        if dry_mode:
            print(json.dumps(wd_object, indent=1))
            self.logger.info("dry mode, no creating wikidata entity")
            return

        cmd = ["wb", "create-entity", "./temp_json_data.json"]
        print(cmd)
        response = subprocess.run(cmd, capture_output=True)
        if '"success":1' not in response.stdout.decode():
            print("error create wikidata, prorably building in wikidata already crated")

            error_response = response.stderr.decode()

            print(error_response)
            if "permissiondenied" in error_response:
                raise ConnectionRefusedError(error_response)

            s = error_response[error_response.find(
                "[["): error_response.find("]]")]

            s = s.replace("[[", "")
            s = s.replace("]]", "")

            wikidata = s.split("|")[0]
            if s == "":
                raise ValueError
            print("building found: https://www.wikidata.org/wiki/" + wikidata)
            return wikidata
            # raise ValueError
        else:
            building_dict_wd = json.loads(response.stdout.decode())
            return building_dict_wd["entity"]["id"]

    def _deprecated_get_wikidata(self, wikidata) -> dict:

        cmd = ['wb', 'gt', '--json', '--no-minimize', wikidata]
        response = subprocess.run(cmd, capture_output=True)
        try:
            object_wd = json.loads(response.stdout.decode())
        except:
            print(response.stdout.decode())
            quit()
        return object_wd

    def get_territorial_entity(self, wd_record) -> dict:
        if 'P131' not in wd_record['claims']:
            return None
        object_wd = self.get_wikidata_simplified(
            wd_record['claims']['P131'][0]['value'])
        return object_wd

    def deprecated_get_territorial_entity(self, wd_record) -> dict:

        try:
            cmd = ['wb', 'gt', '--json', '--no-minimize',
                   wd_record['claims']['P131'][0]['value']]
        except:
            return None
        response = subprocess.run(cmd, capture_output=True)
        try:
            object_wd = json.loads(response.stdout.decode())
        except:
            self.logger.error('check '+' '.join(cmd))
            quit()
        return object_wd

    def get_wikidata_simplified(self, entity_id) -> dict:
        assert entity_id is not None
        # get all claims of this wikidata objects
        if entity_id in self.wikidata_cache['entities_simplified']:
            return self.wikidata_cache['entities_simplified'][entity_id]

        site = pywikibot.Site("wikidata", "wikidata")
        entity = pywikibot.ItemPage(site, entity_id)
        entity.get()

        object_record = {'labels': {}}

        labels_pywikibot = entity.labels.toJSON()
        for lang in labels_pywikibot:
            object_record['labels'][lang] = labels_pywikibot[lang]['value']

        object_record['id'] = entity.getID()
        claims = dict()
        wb_claims = entity.toJSON()['claims']

        for prop_id in wb_claims:
            
            claims[prop_id] = list()
            for claim in wb_claims[prop_id]:

                claim_s=dict()
                claim_s['rank']=claim.get('rank',None)
                if prop_id=='P1813' and entity_id=='Q660770':                
                    pass
                if 'datatype' not in claim['mainsnak']:
                    pass
                    # this is 'somevalue' claim, skip, because it not simply
                elif claim['mainsnak']['datatype'] == 'wikibase-item':
                    claim_s['value'] = 'Q'+str(claim['mainsnak']['datavalue']['value']['numeric-id'])
                elif claim['mainsnak']['datatype'] == 'time':
                    claim_s['value'] = claim['mainsnak']['datavalue']['value']['time'][8:]
                elif claim['mainsnak']['datatype'] == 'external-id':
                    claim_s['value'] = str(claim['mainsnak']['datavalue']['value'])
                elif claim['mainsnak']['datatype'] == 'string':
                    claim_s['value'] = str(claim['mainsnak']['datavalue']['value'])
                elif claim['mainsnak']['datatype'] == 'monolingualtext':
                    claim_s['value'] =  claim['mainsnak']['datavalue']['value']['text'] 
                    claim_s['language'] = str(claim['mainsnak']['datavalue']['value']['language'])
                if 'qualifiers' in claim:  claim_s['qualifiers'] = claim['qualifiers']
                claims[prop_id].append(claim_s)

        object_record['claims'] = claims

        wb_sitelinks = entity.toJSON().get('sitelinks', dict())
        commons_sitelink = ''
        if 'commonswiki' in wb_sitelinks:
            commons_sitelink = wb_sitelinks['commonswiki']['title']

        if "P373" in object_record['claims']:
            object_record['commons'] = object_record["claims"]["P373"][0]["value"]
        elif 'commonswiki' in wb_sitelinks:
            object_record['commons'] = wb_sitelinks['commonswiki']['title'].replace(
                'Category:', '')
        else:
            object_record['commons'] = None

        '''if "en" not in object_wd["labels"]:
            self.logger.error('object https://www.wikidata.org/wiki/' +
                              wikidata+' must have english label')
            return None
        '''

        self.wikidata_cache['entities_simplified'][entity_id] = object_record
        self.wikidata_cache_save(
            self.wikidata_cache, self.wikidata_cache_filename)
        return object_record

    def prev_get_wikidata_simplified(self, wikidata) -> dict:

        # get all claims of this wikidata objects
        if wikidata in self.wikidata_cache['entities_simplified']:
            return self.wikidata_cache['entities_simplified'][wikidata]

        cmd = ["wb", "gt", "--json", "--no-minimize", wikidata]
        response = subprocess.run(cmd, capture_output=True)
        try:
            object_wd = json.loads(response.stdout.decode())
        except:
            self.logger.error('server response not decoded')
            self.logger.error(' '.join(cmd))
            self.logger.error(response.stdout.decode())
            quit()
        object_record = {'labels': {}}
        object_record['labels'] = object_wd["labels"]
        object_record['id'] = object_wd["id"]

        '''if "en" not in object_wd["labels"]:
            self.logger.error('object https://www.wikidata.org/wiki/' +
                              wikidata+' must have english label')
            return None
        '''
        if "P373" in object_wd["claims"]:
            object_record['commons'] = object_wd["claims"]["P373"][0]["value"]
        elif 'commonswiki' in object_wd["sitelinks"]:
            object_record['commons'] = object_wd["sitelinks"]["commonswiki"]["title"].replace(
                'Category:', '')
        else:
            object_record['commons'] = None

        if "P31" in object_wd["claims"]:
            object_record['instance_of_list'] = object_wd["claims"]["P31"]
        object_record['claims'] = object_wd["claims"]

        self.wikidata_cache['entities_simplified'][wikidata] = object_record
        self.wikidata_cache_save(
            self.wikidata_cache, self.wikidata_cache_filename)

        return object_record

    def page_template_taken_on(self, page, location, dry_run=True, interactive=False, verbose=True):
        assert page
        texts = dict()
        page_not_need_change = False
        texts[0] = page.text

        if '.svg'.upper() in page.full_url().upper():
            return False
        if '.png'.upper() in page.full_url().upper():
            return False
        if '.ogg'.upper() in page.full_url().upper():
            return False

        if '{{Information'.upper() not in texts[0].upper():
            self.logger.debug(
                'template Information not exists in '+page.title())
            return False
        if '|location='.upper()+location.upper() in texts[0].upper():
            self.logger.debug('|location='+location+' already in page')
            page_not_need_change = True
            texts[1] = texts[0]
        else:
            try:
                texts[1] = self._text_add_template_taken_on(texts[0])
            except:
                raise ValueError('invalid page text in ' + page.full_url())
        assert 'Taken on'.upper() in texts[1].upper() or 'Taken in'.upper() in texts[1].upper() or 'According to Exif data'.upper(
        ) in texts[1].upper(), 'wrong text in '+page.title()

        datestr = self.get_date_from_pagetext(texts[1])
        if datestr == False:
            return False
        if '/' in datestr:
            raise ValueError(
                'Slash symbols in date causes side-effects. Normalize date in '+page.full_url())
        if len(datestr) < len('yyyy-mm-dd'):
            return False
        if len(datestr) > len('yyyy-mm-dd'):
            return False        
        assert datestr, 'invalid date parce in '+page.full_url()

        location_value_has_already = self._text_get_template_taken_on_location(
            texts[1])

        if location_value_has_already is None:
            texts[2] = self._text_add_template_taken_on_location(
                texts[1], location)
        else:
            texts[2] = self._text_get_template_replace_on_location(
                texts[1], location)

        if texts[2] == False:
            return False
        if '|location='+location+'}}' not in texts[2]:
            return False
        # Remove category
        cat='Russia photographs taken on '+datestr
        texts[2]=texts[2].replace("[[Category:"+cat+"]]",'')
        texts[2]=texts[2].replace("[[Category:"+cat.replace(' ','_')+"]]",'')


        date_obj = datetime.strptime(datestr, '%Y-%m-%d')
        date_obj.strftime('%B %Y')
        cat=date_obj.strftime('%B %Y')+' in '+location
        texts[2]=texts[2].replace("[[Category:"+cat+"]]",'')
        texts[2]=texts[2].replace("[[Category:"+cat.replace(' ','_')+"]]",'')

        cat=date_obj.strftime('%Y')+' in '+location
        texts[2]=texts[2].replace("[[Category:"+cat+"]]",'')
        texts[2]=texts[2].replace("[[Category:"+cat.replace(' ','_')+"]]",'')

        cat=date_obj.strftime('%Y')+' in Russia'
        texts[2]=texts[2].replace("[[Category:"+cat+"]]",'')
        texts[2]=texts[2].replace("[[Category:"+cat.replace(' ','_')+"]]",'')


        self.difftext(texts[0], texts[2])
        if texts[0]!=texts[2]:page_not_need_change = False

        if verbose:
            print('----------- proposed page content ----------- ' +
                  datestr + '--------')

            print(texts[2])
        if not dry_run and not interactive:
            page.text = texts[2]
            if page_not_need_change == False:
                page.save('add {{Taken on location}} template')
            self.create_category_taken_on_day(location, datestr)
        else:
            print('page not changing')

        if interactive:
            answer = input(" do change on  "+page.full_url() + "\n y / n   ? ")
            # Remove white spaces after the answers and convert the characters into lower cases.
            answer = answer.strip().lower()

            if answer in ["yes", "y", "1"]:
                page.text = texts[2]
                page.save('add {{Taken on location}} template')
                self.create_category_taken_on_day(location, datestr)

    def take_user_wikidata_id(self, wdid) -> str:
        warnings.warn('use wikidata_input2id',
                      DeprecationWarning, stacklevel=2)
        # parse user input wikidata string.
        # it may be wikidata id, wikidata uri, string.
        # call search if need
        # return valid wikidata id

        # accept values with hints after #: Q198271#ZIU-9
        if '#' in wdid:
            wdid = wdid[0:wdid.index('#')]

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
        warnings.warn('use wikidata_input2id',
                      DeprecationWarning, stacklevel=2)
        cmd = ['wb', 'search', '--json', text]

        response = subprocess.run(cmd, capture_output=True)
        object_wd = json.loads(response.stdout.decode())
        if stop_on_error:
            if not len(object_wd) > 0:
                raise ValueError('not found in wikidata: '+text)

        return object_wd[0]['id']

    def get_heritage_types(self, country='RU') -> list:
        template = '''
        SELECT ?item ?label ?_image WHERE {
  ?item wdt:P279 wd:Q8346700.
  SERVICE wikibase:label {
    bd:serviceParam wikibase:language "ru" . 
    ?item rdfs:label ?label
  }
}
LIMIT 100
'''
        sparql = template
        site = pywikibot.Site("wikidata", "wikidata")
        repo = site.data_repository()

        generator = pagegenerators.PreloadingEntityGenerator(
            pagegenerators.WikidataSPARQLPageGenerator(sparql, site=repo))
        items_ids = list()
        for item in generator:
            items_ids.append(item.id)
        heritage_types = {"RU": items_ids}
        return heritage_types

    def get_heritage_id(self, wdid) -> str:
        # if wikidata object "heritage designation" is one of "culture heritage in Russia" - return russian monument id
        # for https://www.wikidata.org/wiki/Q113683163 reads P1483, returns '6931214010' or None

        site = pywikibot.Site("wikidata", "wikidata")
        site.login()
        site.get_tokens("csrf")  # preload csrf token
        item = pywikibot.ItemPage(site, wdid)
        item.get()

        if 'P1435' not in item.claims:
            return None
        if 'P1483' not in item.claims:
            return None

        heritage_types = self.get_heritage_types('RU')
        claims = item.claims.get("P1435")
        for claim in claims:
            if claim.getTarget().id in heritage_types['RU']:
                heritage_claim = item.claims.get("P1483")[0]
                return heritage_claim.getTarget()

        return None

    def get_heritage_id_old(self, wikidata) -> str:

        # if wikidata object "heritage designation" is one of "culture heritage in Russia" - return russian monument id

        # get all claims of this wikidata objects
        cmd = ["wb", "gt", "--props", "claims",
               "--json", "--no-minimize", wikidata]
        response = subprocess.run(cmd, capture_output=True)
        try:
            dict_wd = json.loads(response.stdout.decode())
        except:
            return None
        # check heritage status of object
        if "P1435" not in dict_wd["claims"]:
            return None
        if "P1483" not in dict_wd["claims"]:
            return None

        cmd = [
            "wb",
            "query",
            "--property",
            "P279",
            "--object",
            "Q8346700",
            "--format",
            "json",
        ]
        response = subprocess.run(cmd, capture_output=True)
        try:
            heritage_types = {"RU": json.loads(response.stdout.decode())}
        except:
            self.logger.error(' '.join(cmd))
            self.logger.error('error parsing json'+response.stdout.decode())
            self.logger.error(
                'hack for termux. using hardcoded list of russian cultural heritage types from 2022')

            heritage_types = {'RU': (
                "Q23668083",
                "Q105835744",
                "Q105835766",
                "Q105835774")}

        for element in dict_wd["claims"]["P1435"]:
            if element["value"] in heritage_types["RU"]:
                return dict_wd["claims"]["P1483"][0]["value"]

    def wikidata_input2id(self, inp) -> str:
        if inp is None:
            return None

        # detect user input string for wikidata
        # if user print a query - search wikidata
        # returns wikidata id

        inp = self.prepare_wikidata_url(inp)
        if inp.startswith('Q'):
            return self.normalize_wdid(inp)

        # search
        cmd = ['wb', 'search', inp, '--json', '--lang', 'en']
        response = subprocess.run(cmd, capture_output=True)

        try:
            result_wd = json.loads(response.stdout.decode())
        except:
            self.logger.error('error parce json from wikibase query')
            self.logger.error(' '.join(cmd))
            self.logger.error(response.stdout.decode())

        candidates = list()
        for element in result_wd:
            candidates.append(element['id']+' '+element['display']['label']['value'] +
                              ' '+element['display'].get('description', {'value': ''})['value'])
        if len(candidates) == 1:
            selected_url = result_wd[0]['id']
            return selected_url
        else:
            try:
                terminal_menu = TerminalMenu(
                    candidates, title="Select wikidata entity for " + inp)
                menu_entry_index = terminal_menu.show()
            except:
                # special for run in temmux
                menu_entry_index = self.user_select(candidates)
            selected_url = result_wd[menu_entry_index]['id']
        print('For '+inp+' selected 【'+selected_url+' ' +
              result_wd[menu_entry_index].get("description", '[no description]')+'】')

        return selected_url

    def user_select(self, candidates):
        i = 0
        for element in candidates:
            print(str(i).rjust(3)+': '+element)
            i = i+1
        print('Enter a number:')
        result = input()
        return int(result.strip())

    def prepare_wikidata_url(self, wikidata) -> str:
        # convert string https://www.wikidata.org/wiki/Q4412648 to Q4412648

        wikidata = str(wikidata).strip()
        wikidata = wikidata.replace('https://www.wikidata.org/wiki/', '')
        if wikidata[0].isdigit() and not wikidata.upper().startswith('Q'):
            wikidata = 'Q'+wikidata
        return wikidata

    def difftext(self, text1, text2):
        l = 0
        is_triggered = 0
        text1_dict = {i: text1.splitlines()[i] for i in range(len(text1.splitlines()))}
        text2_dict = {i: text2.splitlines()[i] for i in range(len(text2.splitlines()))}
        
        for l in range(0, len(text1.splitlines())):
            if text1_dict.get(l,' - - - - - void string - - - ') != text2_dict.get(l,' - - - - - void string - - - '):
                is_triggered += 1
                if is_triggered == 1:
                    print()
                print(text1_dict.get(l,' - - - - - void string - - - '))
                print(text2_dict.get(l,' - - - - - void string - - - '))
                print('^^^^^text changed^^^^^')

    def _text_get_template_replace_on_location(self, test_str, location):
        import re

        regex = r"^.*(?:Information|photograph)[\s\S]*?Date\s*?=.*location=(?P<datecontent>[\s\S]*?)[\|\}}\n].*$"

        matches = re.finditer(regex, test_str, re.UNICODE |
                              re.MULTILINE | re.IGNORECASE)

        for matchNum, match in enumerate(matches, start=1):

            for groupNum in range(0, len(match.groups())):
                groupNum = groupNum + 1

                groupstart = match.start(groupNum)
                groupend = match.end(groupNum)
                content = match.group(groupNum)

        text = test_str[0:groupstart] + location+test_str[groupend:]
        return text

    def _text_get_template_taken_on_location(self, test_str):
        # return content of "location" if exists

        import re

        regex = r"^.*(?:Information|photograph)[\s\S]*?Date\s*?=.*location=(?P<datecontent>[\s\S]*?)[\|\}}\n].*$"

        matches = re.search(regex, test_str, re.IGNORECASE |
                            re.UNICODE | re.MULTILINE)

        if matches:

            for groupNum in range(0, len(matches.groups())):
                groupNum = groupNum + 1

                return (matches.group(groupNum))

    def is_taken_on_in_text(self, test_str):
        import re

        regex = r"^.*(?:Information|photograph)[\s\S]*?Date\s*?=.*?(taken on|According to Exif data)\s*?[\|\n].*$"

        matches = re.search(regex, test_str, re.IGNORECASE |
                            re.UNICODE | re.MULTILINE)

        if matches:

            for groupNum in range(0, len(matches.groups())):
                groupNum = groupNum + 1

                if matches.group(groupNum) is not None:
                    return True
        return False

    def _text_add_template_taken_on(self, test_str):
        assert test_str

        if self._text_get_template_taken_on_location(test_str) is not None:
            return test_str
        if self.is_taken_on_in_text(test_str):
            return test_str
        # test_str name comes from onine regex editor
        import re

        regex = r"^.*(?:Information|photograph)[\s\S]*?Date\s*?=(?P<datecontent>[\s\S]*?)[\|\n].*$"

        matches = re.finditer(regex, test_str, re.UNICODE |
                              re.MULTILINE | re.IGNORECASE)

        for matchNum, match in enumerate(matches, start=1):

            for groupNum in range(0, len(match.groups())):
                groupNum = groupNum + 1

                groupstart = match.start(groupNum)
                groupend = match.end(groupNum)
                content = match.group(groupNum)

        text = test_str[0:groupstart] + \
            ' {{Taken on|'+content.strip()+"}}"+test_str[groupend:]
        return text

    def input2list_wikidata(self, inp):

        if inp is None or inp == False:
            return list()
        if isinstance(inp, str):
            inp = ([inp])
        secondary_wikidata_ids = list()
        for inp_wikidata in inp:
            wdid = self.wikidata_input2id(inp_wikidata)
            secondary_wikidata_ids.append(wdid)
        return secondary_wikidata_ids

    def _text_add_template_taken_on_location(self, test_str, location):

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
                content = match.group(groupNum)

        text = test_str[0:groupstart] + '|location=' + \
            location+""+test_str[groupend:]
        return text

    def get_date_from_pagetext(self, test_str) -> str:
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

    def create_category_taken_on_day(self, location, yyyymmdd):
        location = location.title()
        if len(yyyymmdd) != 10:
            return False

        categoryname = '{location}_photographs_taken_on_{yyyymmdd}'.format(
            location=location, yyyymmdd=yyyymmdd)

        pagename = 'Category:'+categoryname

        if location == 'Moscow':
            content = '{{Moscow photographs taken on navbox}}'
        else:
            content = '{{'+location+' photographs taken on navbox|' + \
                yyyymmdd[0:4]+'|'+yyyymmdd[5:7]+'|'+yyyymmdd[8:10]+'}}'
        # self.create_page(pagename, content, 'create category')
        self.create_category(pagename, content)

        if location in ('Moscow', 'Moscow Oblast', 'Saint Petersburg','Tatarstan','Nizhny Novgorod Oblast','Leningrad Oblast'):
            self.create_category_taken_on_day('Russia', yyyymmdd)

    def create_category(self, pagename: str, content: str):
        if not pagename.startswith('Category:'):
            pagename = 'Category:'+pagename
        if not self.is_category_exists(pagename):
            self.create_page(pagename, content, 'create category')
        else:
            self.logger.info('page already exists '+pagename)

    def is_category_exists(self, categoryname):
        if not categoryname.startswith('Category:'):
            categoryname = 'Category:'+categoryname
        # check in cache
        if categoryname in self.wikidata_cache['commonscat_exists_set']:
            return True

        site = pywikibot.Site("commons", "commons")
        site.login()
        site.get_tokens("csrf")  # preload csrf token
        page = pywikibot.Page(site, title=categoryname)

        if page.exists():
            self.wikidata_cache['commonscat_exists_set'].add(categoryname)
            self.wikidata_cache_save(
                self.wikidata_cache, self.wikidata_cache_filename)

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

    def get_building_record_wikidata(self, wikidata, stop_on_error=False) -> dict:
        building_wd = self.get_wikidata_simplified(wikidata)

        # get street of object
        if "P669" not in building_wd["claims"]:
            if stop_on_error:
                raise ValueError(
                    "object https://www.wikidata.org/wiki/"
                    + wikidata
                    + "should have street"
                )
            else:
                return None

        street_wd = self.get_wikidata_simplified(
            building_wd["claims"]["P669"][0]["value"])

        building_record = {
            "building": "yes",
            "addr:street:ru": street_wd["labels"]["ru"],
            "addr:street:en": street_wd["labels"]["en"],
            "addr:housenumber:local": building_wd["claims"]["P669"][0]["qualifiers"][
                "P670"
            ][0]['datavalue']["value"],
            "addr:housenumber:en": translit(
                building_wd["claims"]["P669"][0]["qualifiers"]["P670"][0]['datavalue']["value"],
                "ru",
                reversed=True,
            ),
        }
        if "P373" in building_wd["claims"]:
            building_record['commons'] = building_wd["claims"]["P373"][0]["value"]
        elif 'commonswiki' in building_wd["sitelinks"]:
            building_record['commons'] = building_wd["sitelinks"]["commonswiki"]["title"].replace(
                'Category:', '')

        return building_record

    def get_best_claim(self, wdid, prop) -> str:
        assert prop.startswith('P')
        entity=self.get_wikidata_simplified(wdid)
        claims=entity['claims'].get(prop)
        for claim in claims:
            if claim['rank']=='preferred':
                return claim['value']
        for claim in claims:
            return claim['value']

    def get_upper_location_wdid(self, wdobj):
        if 'P131' in wdobj['claims']:
            return self.get_best_claim(wdobj['id'], 'P131')
            # return self.get_wd_by_wdid(wdobj['claims']['P131'][0]['value'])

        return None

    def normalize_wdid(self, object_wdid: str) -> str:
        # convert Q1021645#office_building to Q1021645
        if '#' not in object_wdid:
            return object_wdid
        else:
            return object_wdid[0:object_wdid.find('#')]

    def get_category_object_in_location(self, object_wdid, location_wdid, order: str = None, verbose=False) -> str:
        object_wdid = self.normalize_wdid(object_wdid)
        cache_key = str(object_wdid)+'/'+location_wdid
        if cache_key in self.cache_category_object_in_location:
            text = ''+self.cache_category_object_in_location[cache_key]+''
            if order:
                text = text+'|'+order
            return text
        stop_hieraechy_walk = False
        cnt = 0
        object_wd = self.get_wikidata_simplified(object_wdid)
        geoobject_wd = self.get_wikidata_simplified(location_wdid)
        while not stop_hieraechy_walk:
            cnt = cnt+1
            if cnt > 9:
                stop_hieraechy_walk = True
            if verbose:
                info = 'search category for union ' + \
                    str(object_wd['labels'].get('en', object_wd['id']))+' ' + \
                    str(geoobject_wd['labels'].get(
                        'en', geoobject_wd['id'])[0:40].rjust(40))
                print(info)
                # self.logger.info(info)

            union_category_name = self.search_commonscat_by_2_wikidata(
                object_wdid, geoobject_wd['id'])
            if union_category_name is not None:
                print('found ' + '[[Category:'+union_category_name+']]')
                self.cache_category_object_in_location[cache_key] = union_category_name
                text = ''+union_category_name+''
                if order:
                    text = text+'|'+order
                return text

            upper_wdid = self.get_upper_location_wdid(geoobject_wd)
            if upper_wdid is None:
                stop_hieraechy_walk = True
                continue
            upper_wd = self.get_wikidata_simplified(upper_wdid)
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
        commonsfilename = fileprocessor.prepare_commonsfilename(
            commonsfilename)

        site = pywikibot.Site("commons", "commons")
        site.login()
        site.get_tokens("csrf")  # preload csrf token
        page = pywikibot.Page(site, title=commonsfilename, ns=6)
        media_identifier = "M{}".format(page.pageid)

        # fetch exist structured data

        request = site.simple_request(
            action="wbgetentities", ids=media_identifier)
        try:
            raw = request.submit()
        except:
            self.logger.error(traceback.format_exc())
            return None

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

        return True

    def wikidata_set_building_entity_name(self, wdid, city_en):
        '''
        change names and aliaces of wikidata entity for building created by SNOW https://ru-monuments.toolforge.org/snow/index.php?id=6330122000

        User should manually enter LOCATED ON STREET with HOUSE NUMBER

        Source:
        https://www.wikidata.org/wiki/Q113683138
        Жилой дом (Тверь)

        Result:
        name ru     Тверь, улица Достоевского 30
        name en     Tver Dostoevskogo street 30
        alias (ru)  [Жилой дом (Тверь)]

        '''
        site = pywikibot.Site("wikidata", "wikidata")
        site.login()
        site.get_tokens("csrf")  # preload csrf token
        item = pywikibot.ItemPage(site, wdid)
        item.get()

        assert ('en' not in item.labels)
        assert ('ru' in item.labels)
        assert 'P669' in item.claims
        claims = item.claims.get("P669")
        for claim in claims:
            # Print the street address value
            # print(claim.getTarget().id)
            street_id = claim.getTarget().id
            try:
                street_name_en = claim.getTarget().labels['en']
            except:
                raise ValueError(
                    'you should set label en at https://www.wikidata.org/wiki/'+claim.getTarget().id+'')
                quit()
            street_name_ru = claim.getTarget().labels['ru']

            # Get the qualifiers of P670
            qualifiers = claim.qualifiers.get("P670")

            # Loop through the qualifiers
            for qualifier in qualifiers:
                # Print the postal code value
                housenumber = qualifier.getTarget()

        print(street_name_en, street_name_ru, housenumber)

        entitynames = dict()
        labels = dict()
        labels['en'] = street_name_en+' '+housenumber
        labels['ru'] = street_name_ru+' '+housenumber
        aliases = item.aliases
        if 'ru' not in aliases:
            aliases['ru'] = list()
        aliases['ru'].append(item.labels['ru'])
        item.editAliases(aliases=aliases, summary="Move name to alias")
        item.editLabels(
            labels=labels, summary="Set name from address P669+P670")
        item.editDescriptions(
            descriptions={"en": "Building in "+city_en}, summary="Edit description")
        '''
        claimStreet = item.claims["P669"][0].getTarget()
        print(claimStreet)
        qualifiers = claimStreet.qualifiers.get("P670")
        for qualifier in qualifiers:
            print(qualifier.getTarget())
        '''

        return

        # Edit the entity name in English
        item.editLabels(labels={"en": "Douglas Noel Adams"},
                        summary="Edit entity name")

        # Add an entity alias in English
        item.editAliases(
            aliases={"en": ["DNA", "Doug"]}, summary="Add entity alias")
        item.editDescriptions(
            descriptions={"en": "British author and humorist"}, summary="Edit description")

    def create_wikidata_object_for_bylocation_category(self, category, wikidata1, wikidata2):
        assert category.startswith(
            'Category:'), 'category should start with Category:  only'
        assert wikidata1.startswith('Q'), 'wikidata1 should start from Q only'
        assert wikidata2.startswith('Q'), 'wikidata2 should start from Q only'
        category_name = category.replace('Category:', '')

        site = pywikibot.Site("wikidata", "wikidata")
        repo = site.data_repository()
        new_item = pywikibot.ItemPage(site)
        label_dict = {"en": category_name}
        new_item.editLabels(labels=label_dict, summary="Setting labels")

        # CLAIM
        claim = pywikibot.Claim(repo, 'P31')
        # This is Wikimedia category
        target = pywikibot.ItemPage(repo, "Q4167836")
        claim.setTarget(target)  # Set the target value in the local object.
        # Inserting value with summary to Q210194
        new_item.addClaim(claim, summary='This is 	Wikimedia category')
        del claim
        del target

        # CLAIM
        claim = pywikibot.Claim(repo, 'P971')
        # category combines topics
        target = pywikibot.ItemPage(repo, wikidata1)
        claim.setTarget(target)  # Set the target value in the local object.
        # Inserting value with summary to Q210194
        new_item.addClaim(claim, summary='This is 	Wikimedia category')
        claim = pywikibot.Claim(repo, 'P971')
        # category combines topics
        target = pywikibot.ItemPage(repo, wikidata2)
        claim.setTarget(target)  # Set the target value in the local object.
        # Inserting value with summary to Q210194
        new_item.addClaim(claim, summary='This is 	Wikimedia category')

        # SITELINK
        sitedict = {'site': 'commonswiki', 'title': category}
        new_item.setSitelink(sitedict, summary=u'Setting commons sitelink.')
        wikidata_id = new_item.getID()

        # ADD Wikidata infobox to commons
        site = pywikibot.Site("commons", "commons")
        site.login()
        site.get_tokens("csrf")  # preload csrf token
        pagename = self.page_name_canonical(category)
        page = pywikibot.Page(site, title=pagename)

        commons_pagetext = page.text
        if '{{Wikidata infobox}}' not in commons_pagetext:
            commons_pagetext = "{{Wikidata infobox}}\n"+commons_pagetext
        page.text = commons_pagetext
        page.save('add {{Wikidata infobox}} template')

    def search_commonscat_by_2_wikidata(self, abstract_wdid, geo_wdid):

        if abstract_wdid in self.wikidata_cache['commonscat_by_2_wikidata']:
            if geo_wdid in self.wikidata_cache['commonscat_by_2_wikidata'][abstract_wdid]:
                return self.wikidata_cache['commonscat_by_2_wikidata'][abstract_wdid][geo_wdid]

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

        generator = pagegenerators.PreloadingEntityGenerator(
            pagegenerators.WikidataSPARQLPageGenerator(sparql, site=repo))
        for item in generator:
            item_dict = item.get()
            try:
                commonscat = item.getSitelink('commonswiki')
            except:
                claim_list = item_dict["claims"].get('P373', ())
                assert claim_list is not none, 'https://www.wikidata.org/wiki/' + \
                    abstract_wdid + ' must have P373commons'
                for claim in claim_list:
                    commonscat = claim.getTarget()
            commonscat = commonscat.replace('Category:', '')

            if abstract_wdid not in self.wikidata_cache['commonscat_by_2_wikidata']:
                self.wikidata_cache['commonscat_by_2_wikidata'][abstract_wdid] = {
                }
            self.wikidata_cache['commonscat_by_2_wikidata'][abstract_wdid][geo_wdid] = commonscat
            self.wikidata_cache_save(
                self.wikidata_cache, self.wikidata_cache_filename)
            return commonscat
        if abstract_wdid not in self.wikidata_cache['commonscat_by_2_wikidata']:
            self.wikidata_cache['commonscat_by_2_wikidata'][abstract_wdid] = {}
        self.wikidata_cache['commonscat_by_2_wikidata'][abstract_wdid][geo_wdid] = None
        self.wikidata_cache_save(
            self.wikidata_cache, self.wikidata_cache_filename)
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
