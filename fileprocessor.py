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
import tempfile
import warnings


class Fileprocessor:
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger(__name__)
    pp = pprint.PrettyPrinter(indent=4)

    exiftool_path = "exiftool"

    wikidata_cache = dict()
    optional_langs = ('de', 'fr', 'it', 'es', 'pt', 'uk', 'be','ja')
    chunk_size = 102400
    photographer = 'Artem Svetlov'


    def input2filelist(self,filepath):
        if os.path.isfile(filepath):
            files = [filepath]
            assert os.path.isfile(filepath)
            uploaded_folder_path = os.path.join(os.path.dirname(filepath),'commons_uploaded')
        elif os.path.isdir(filepath):
            files = os.listdir(filepath)
            files = [os.path.join(filepath, x) for x in files]
            files = list(filter(lambda name: 'commons_uploaded' not in name , files))

            
            uploaded_folder_path = os.path.join(filepath,'commons_uploaded')
        else:
            raise Exception("filepath should be file or directory")
        return files, uploaded_folder_path
    
    
    def prepare_wikidata_url(self, wikidata) -> str:
        # convert string https://www.wikidata.org/wiki/Q4412648 to Q4412648

        wikidata = str(wikidata).strip()
        wikidata = wikidata.replace('https://www.wikidata.org/wiki/', '')

        return wikidata

    def upload_file(self, filepath, commons_name, description, verify_description=True):
        # The site object for Wikimedia Commons
        site = pywikibot.Site("commons", "commons")

        # The upload robot object
        bot = UploadRobot(
            [filepath],  # A list of files to upload
            description=description,  # The description of the file
            use_filename=commons_name,  # The name of the file on Wikimedia Commons
            keep_filename=True,  # Keep the filename as is
            # Ask for verification of the description
            verify_description=verify_description,
            targetSite=site,  # The site object for Wikimedia Commons
            chunk_size=self.chunk_size,
        )

        # Try to run the upload robot
        try:
            bot.run()
        except Exception as e:
            # Handle API errors
            print(f"API error: {e.code}: {e.info}")

    def get_building_record_wikidata(self, wikidata) -> dict:
        warnings.warn('moved to model_wiki', DeprecationWarning, stacklevel=2)
        # get all claims of this wikidata objects
        cmd = ["wb", "gt", "--props", "claims",
               "--json", "--no-minimize", wikidata]
        response = subprocess.run(cmd, capture_output=True)
        building_wd = json.loads(response.stdout.decode())

        # get street of object
        if "P669" not in building_wd["claims"]:
            raise ValueError(
                "object https://www.wikidata.org/wiki/"
                + wikidata
                + "should have street"
            )

        cmd = [
            "wb",
            "gt",
            "--json",
            "--no-minimize",
            building_wd["claims"]["P669"][0]["value"],
        ]
        response = subprocess.run(cmd, capture_output=True)
        street_wd = json.loads(response.stdout.decode())

        building_record = {
            "building": "yes",
            "addr:street:ru": street_wd["labels"]["ru"],
            "addr:street:en": street_wd["labels"]["en"],
            "addr:housenumber:local": building_wd["claims"]["P669"][0]["qualifiers"][
                "P670"
            ][0]["value"],
            "addr:housenumber:en": translit(
                building_wd["claims"]["P669"][0]["qualifiers"]["P670"][0]["value"],
                "ru",
                reversed=True,
            ),
            "commons": building_wd["claims"]["P373"][0]["value"],
        }

        return building_record


    
    
    def get_wikidata_simplified(self, wikidata) -> dict:
        warnings.warn('moved to model_wiki', DeprecationWarning, stacklevel=2)
        # get all claims of this wikidata objects

        if wikidata in self.wikidata_cache:
            return self.wikidata_cache[wikidata]

        cmd = ["wb", "gt", "--json", "--no-minimize", wikidata]
        response = subprocess.run(cmd, capture_output=True)
        object_wd = json.loads(response.stdout.decode())
        object_record = {'names': {}}
        try:
            object_record['names'] = {
                "en": object_wd["labels"]["en"],
                "ru": object_wd["labels"]["ru"],
            }
        except:
            self.logger.error('object https://www.wikidata.org/wiki/' +
                              wikidata+' must has name ru and name en')
            quit()

        for lang in self.optional_langs:
            if lang in object_wd["labels"]:
                object_record['names'][lang] = object_wd["labels"][lang]
        if "P373" in object_wd["claims"]:
            object_record['commons'] = object_wd["claims"]["P373"][0]["value"]
        elif 'commonswiki' in object_wd["sitelinks"]:
            object_record['commons'] = object_wd["sitelinks"]["commonswiki"]["title"].replace('Category:','')
        else:
            object_record['commons'] = None
                              
        if "P31" in object_wd["claims"]:
            object_record['instance_of_list'] = object_wd["claims"]["P31"]
        self.wikidata_cache[wikidata] = object_record

        return object_record

    def is_wikidata_id(self, text) -> bool:
        warnings.warn('moved to model_wiki', DeprecationWarning, stacklevel=2)
        # check if string is valid wikidata id
        if text.startswith('Q') and text[1:].isnumeric():
            return True
        else:
            return False

    def search_wikidata_by_string(self, text, stop_on_error=True) -> str:
        warnings.warn('moved to model_wiki', DeprecationWarning, stacklevel=2)
        cmd = ['wb', 'search', '--json', text]

        response = subprocess.run(cmd, capture_output=True)
        object_wd = json.loads(response.stdout.decode())
        if stop_on_error:
            if not len(object_wd) > 0:
                raise ValueError('not found in wikidata: '+text)
        self.logger.debug('found: '+text+' '+object_wd[0]['concepturi'])
        return object_wd[0]['id']

    def get_wikidata_labels(self, wikidata) -> dict:
        warnings.warn('moved to model_wiki', DeprecationWarning, stacklevel=2)
        cmd = ['wb', 'gt', '--props', 'labels', '--json', wikidata]
        response = subprocess.run(cmd, capture_output=True)
        object_wd = json.loads(response.stdout.decode())
        return object_wd['labels']

    def get_wikidata(self, wikidata) -> dict:
        warnings.warn('moved to model_wiki', DeprecationWarning, stacklevel=2)
        cmd = ['wb', 'gt', '--json', '--no-minimize', wikidata]
        response = subprocess.run(cmd, capture_output=True)
        object_wd = json.loads(response.stdout.decode())
        return object_wd

    def get_territorial_entity(self, wd_record) -> dict:
        warnings.warn('moved to model_wiki', DeprecationWarning, stacklevel=2)
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

    def make_image_texts_vehicle(self, filename, vehicle,  model, street, number, system=None, city=None, route=None, location=None, line=None, rail=None, facing=None, color_list=None) -> dict:
        assert os.path.isfile(filename)

        vehicle_names = {'ru': {'tram': 'трамвай', 'trolleybus': 'троллейбус',
                           'bus': 'автобус', 'train': 'поезд', 'locomotive':'локомотив', 'auto': 'автомобиль', 'plane': 'самолёт'}}
        wikidata_4_structured_data = list()
        
        assert facing in ('Left','Right',None)

        if model is not None:
            if self.is_wikidata_id(model):
                model_wdid = model
            else:
                model_wdid = self.search_wikidata_by_string(
                    model, stop_on_error=True)
            model_wd = self.get_wikidata(model_wdid)
            model_names = model_wd["labels"]
            wikidata_4_structured_data.append(model_wd['id'])

        if self.is_wikidata_id(street):
            street_wdid = street
        else:
            street_wdid = self.search_wikidata_by_string(
                street, stop_on_error=True)
        street_wd = self.get_wikidata(street_wdid)
        street_names = street_wd["labels"]
        wikidata_4_structured_data.append(street_wd['id'])

        if system is not None:
            if self.is_wikidata_id(system):
                system_wdid = system
            else:
                system_wdid = self.search_wikidata_by_string(
                    system, stop_on_error=True)
            system_wd = self.get_wikidata(system_wdid)
            system_names = system_wd["labels"]
            wikidata_4_structured_data.append(system_wd['id'])
            city_name_en = self.get_territorial_entity(system_wd)[
                'labels']['en']
            city_name_ru = self.get_territorial_entity(system_wd)[
                'labels']['ru']

        elif system is None:

            city_wd = self.get_territorial_entity(street_wd)

            city_name_en = city_wd['labels']['en']
            city_name_ru = city_wd['labels']['ru']

            wikidata_4_structured_data.append(city_wd['id'])

        line_wdid = None
        if line is not None:
            if self.is_wikidata_id(line):
                line_wdid = line
            else:
                line_wdid = self.search_wikidata_by_string(
                    line, stop_on_error=True)

            wikidata_4_structured_data.append(line_wdid)

        objectname_en = '{city} {transport} {model} {number}'.format(
            transport=vehicle,
            city=city_name_en,
            model=model_names['en'],
            number=number
        )

        objectname_ru = '{city}, {transport} {model} {number}'.format(
            city=city_name_ru,
            transport=vehicle_names['ru'][vehicle],
            model=model_names.get('ru', model_names['en']),
            number=number
        )

        # obtain exif
        dt_obj = self.image2datetime(filename)
        geo_dict = self.image2coords(filename)

        filename_base = os.path.splitext(os.path.basename(filename))[0]
        filename_extension = os.path.splitext(os.path.basename(filename))[1]
        commons_filename = (
            objectname_en + " " +
            dt_obj.strftime("%Y-%m %s") + filename_extension
        )

        text = ''

        st = """== {{int:filedesc}} ==
{{Information
|description="""
        st += "{{en|1=" + objectname_en + ' on ' + street_names['en']
        if route is not None:
            st += ' Line '+route
        if line_wdid is not None:
            st += ' '+self.get_wikidata(line_wdid)['labels']['en']
        st += "}}"
        st += "{{ru|1=" + objectname_ru + ' на ' + \
            street_names['ru'].replace(
                'Улица', 'улица').replace('Проспект', 'проспект')
        if route is not None:
            st += ' Маршрут '+route
        if line_wdid is not None:
            st += ' '+self.get_wikidata(line_wdid)['labels']['ru']

        st += "}}"

        st += "\n"
        st += (
            """|source={{own}}
|author={{Creator:Artem Svetlov}}
|date="""
            + "{{Taken on|"
            + dt_obj.isoformat()
            + "|location="
            + location
            + "|source=EXIF}}"
            + "\n"
        )
        st += "}}\n"

        text += st

        if geo_dict is not None:
            st = (
                "{{Location dec|"
                + str(geo_dict.get("lat"))
                + "|"
                + str(geo_dict.get("lon"))
            )
            if "direction" in geo_dict:
                st += "|heading:" + str(geo_dict.get("direction"))
            st += "}}\n"
            text += st

            if "dest_lat" in geo_dict:
                st = (
                    "{{object location|"
                    + str(geo_dict.get("dest_lat"))
                    + "|"
                    + str(geo_dict.get("dest_lon"))
                    + "}}"
                    + "\n"
                )
                text += st
        text += self.get_camera_text(filename)
        """
        make
        model
        f_number
        lens_model

        """

        text = (
            text
            + """== {{int:license-header}} ==
{{self|cc-by-sa-4.0|author=Artem Svetlov}}
"""
        )

        transports = {
        'tram': 'Trams', 
        'trolleybus': 'Trolleybuses',
      'bus': 'Buses',
      'train': 'Rail vehicles',
      'locomotive': 'Locomotives',
      'auto':'Automobiles'
                      }
        if route is not None:
            text = text + "[[Category:{transports} on route {route} in {city}]]".format(
                transports=transports[vehicle],
                route=route,
                city=city_name_en) + "\n"
        if 'system_wd' in locals():
            text = text + \
                "[[Category:" + system_wd["claims"]["P373"][0]["value"] + "]]" + "\n"
        # category for model. search for category like "ZIU-9 in Moscow"
        from model_wiki import Model_wiki  as Model_wiki_ask
        modelwiki = Model_wiki_ask()
        
        cat = modelwiki.get_category_object_in_location(model_wd['id'],street_wd['id'],verbose=True)
        if cat is not None: 
            text = text + cat + "\n"
        else:
            text = text + \
                "[[Category:" + model_wd["claims"]["P373"][0]["value"] + "]]" + "\n"
        try:
            text = text + \
                "[[Category:" + street_wd["claims"]["P373"][0]["value"] + "]]" + "\n"
        except:
            pass
        text = text + "[[Category:Photographs by " + \
            self.photographer+'/'+location+"]]" + "\n"
        if line is not None:
            text = text + \
                "[[Category:" + \
                self.get_wikidata(line_wdid)[
                    "claims"]["P373"][0]["value"]+"]]" + "\n"

        # locale.setlocale(locale.LC_ALL, 'en_GB')
        if vehicle in ('train','locomotive'):
            text += "[[Category:Railway photographs taken on " + \
                dt_obj.strftime("%Y-%m-%d")+"]]" + "\n"
            if isinstance(location, str):
                text += "[[Category:" + \
                    dt_obj.strftime("%B %Y") + \
                    " in rail transport in "+location+"]]" + "\n"

        if vehicle == 'tram':
            text += "[[Category:Railway photographs taken on " + \
                dt_obj.strftime("%Y-%m-%d")+"]]" + "\n"
            if isinstance(location, str):
                text += "[[Category:" + \
                    dt_obj.strftime("%B %Y") + \
                    " in tram transport in "+location+"]]" + "\n"
        
        if facing is not None:
            facing = facing.strip().capitalize()
            assert facing.strip().upper() in ('LEFT','RIGHT')
            
            text += "[[Category:"+transports[vehicle]+" facing " +  facing.lower() + "]]\n"  
            if facing == 'Left': wikidata_4_structured_data.append('Q119570753')
            if facing == 'Right': wikidata_4_structured_data.append('Q119570670')
        if color_list is not None:
            
            colorname = ''
            colorname = ' and '.join(color_list.sort())
            colorname = colorname.lower().capitalize()
            text += "[[Category:{colorname} {transports}]]\n".format(
            transports = transports[vehicle].lower(),
            colorname = colorname)
            
        if number is not None:
            text += "[[Category:Number "+number+" on vehicles]]\n"
        if dt_obj is not None:
            text += "[[Category:{transports} in {location} photographed in {year}]]\n".format(
            transports = transports[vehicle],
            location = location,
            year = dt_obj.strftime("%Y"),
            )


        return {"name": commons_filename, "text": text, "structured_data_on_commons": wikidata_4_structured_data, "dt_obj": dt_obj}

    def get_date_information_part(self, dt_obj, taken_on_location):
        st = ''
        st += (
            """|source={{own}}
|author={{Creator:""" + self.photographer+"""}}
|date="""
            + "{{Taken on|"
            + dt_obj.isoformat()
            + "|location="
            + taken_on_location
            + "|source=EXIF}}"
            + "\n"
        )
        return st

    def get_tech_templates(self, filename, geo_dict, country):
        text = ''
        if 'stitch' in filename:
            text = text + "{{Panorama}}" + "\n"

        if geo_dict is not None:
            st = (
                "{{Location dec|"
                + str(geo_dict.get("lat"))
                + "|"
                + str(geo_dict.get("lon"))
            )
            if "direction" in geo_dict:
                st += "|heading:" + str(geo_dict.get("direction"))
            st += "}}\n"
            text += st

            if "dest_lat" in geo_dict:
                st = (
                    "{{object location|"
                    + str(geo_dict.get("dest_lat"))
                    + "|"
                    + str(geo_dict.get("dest_lon"))
                    + "}}"
                    + "\n"
                )
                text += st
        text += self.get_camera_text(filename)

        text = (
            text
            + """== {{int:license-header}} ==
{{self|cc-by-sa-4.0|author=""" + self.photographer+"""}}
"""
        )

        text = text + "[[Category:Photographs by " + \
            self.photographer+'/'+country+"]]" + "\n"
        if 'ShiftN' in filename:
            text = text + "[[Category:Corrected with ShiftN]]" + "\n"
        if 'stitch' in filename:
            text = text + "[[Category:Photographs by " + \
                self.photographer+'/Stitched panoramics]]' + "\n"

        return text

    def make_image_texts_building(
        self, filename, wikidata, place_en, place_ru, no_building=False, country='', photographer='Artem Svetlov', rail=''
    ) -> dict:
        # return file description texts
        # there is no excact 'city' in wikidata, use manual input cityname

        #from model_wiki import Model_wiki
        #modelwiki = Model_wiki()
    
        assert os.path.isfile(filename), 'not found '+filename

        # obtain exif
        dt_obj = self.image2datetime(filename)
        geo_dict = self.image2coords(filename)

        if no_building:
            #wdid = modelwiki.wikidata_input2id(wikidata)
            wd_record = self.get_wikidata_simplified(wikidata)

        else:
            wd_record = self.get_wikidata_simplified(wikidata)
            wd_record_building = self.get_building_record_wikidata(wikidata)
            self.pp.pprint(wd_record_building)
        instance_of_data = list()

        if 'instance_of_list' in wd_record:
            for i in wd_record['instance_of_list']:
                instance_of_data.append(
                    self.get_wikidata_simplified(i['value']))

        text = ""
        objectnames = {}
        if no_building:
            objectnames['en'] = wd_record['names']["en"]
            objectnames['ru'] = wd_record['names']["ru"]
            for lang in self.optional_langs:
                if lang in wd_record['names']:
                    objectnames[lang] = wd_record['names'][lang]
        else:
            objectnames['en'] = (
                place_en
                + " "
                + wd_record_building["addr:street:en"]
                + " "
                + wd_record_building["addr:housenumber:en"]
            )
            objectnames['ru'] = (
                place_ru
                + " "
                + wd_record_building["addr:street:ru"]
                + " "
                + wd_record_building["addr:housenumber:local"]
            )

        objectname_long_ru = objectnames['ru']
        objectname_long_en = objectnames['en']
        # TODO change objectname_long_en to objectnames_long[en]
        objectnames_long = {}
        if len(instance_of_data) > 0:
            objectname_long_ru = ', '.join(
                d['names']['ru'] for d in instance_of_data) + ' '+objectnames['ru']
            objectname_long_en = ', '.join(
                d['names']['en'] for d in instance_of_data) + ' '+objectnames['en']
            for lang in self.optional_langs:
                try:
                    objectnames_long[lang] = ', '.join(
                        d['names'][lang] for d in instance_of_data) + ' '+objectnames[lang]
                except:
                    pass
        filename_base = os.path.splitext(os.path.basename(filename))[0]
        filename_extension = os.path.splitext(os.path.basename(filename))[1]
        commons_filename = (
            objectnames['en'] + " " +
            dt_obj.strftime("%Y-%m %s") + filename_extension
        )
        commons_filename = commons_filename.replace("/", " drob ")

        prototype = """== {{int:filedesc}} ==
{{Information
|description={{en|1=2nd Baumanskaya Street 1 k1}}{{ru|1=Вторая Бауманская улица дом 1 К1}} {{ on Wikidata|Q86663303}}  {{Building address|Country=RU|Street name=2-я Бауманская улица|House number=1 К1}}  
|source={{own}}
|author={{Creator:Artem Svetlov}}
|date={{According to Exif data|2022-07-03|location=Moscow}}
}}

{{Location|55.769326012498155|37.68742327500131}}
{{Taken with|Pentax K10D|sf=1|own=1}}

{{Photo Information
 |Model                 = Olympus mju II
 |ISO                   = 200
 |Lens                  = 
 |Focal length          = 35
 |Focal length 35mm     = 35
 |Support               = freehand
 |Film                  = Kodak Gold 200
 |Developer             = C41
 }}
 
    == {{int:license-header}} ==
    {{self|cc-by-sa-4.0|author=Артём Светлов}}

    [[Category:2nd Baumanskaya Street 1 k1]]
    [[Category:Photographs by Artem Svetlov/Moscow]]

    """
        st = """== {{int:filedesc}} ==
{{Information
|description="""
        st += "{{en|1=" + objectname_long_en + "}} \n"
        st += "{{ru|1=" + objectname_long_ru + "}} \n"
        for lang in self.optional_langs:
            if lang in objectnames_long:
                st += "{{"+lang+"|1=" + objectnames_long[lang] + "}} \n"
        heritage_id = None
        heritage_id = self.get_heritage_id(wikidata)
        if heritage_id is not None:
            st += "{{Cultural Heritage Russia|" + heritage_id + "}}"
        st += " {{ on Wikidata|" + wikidata + "}}"
        st += "\n"
        st += self.get_date_information_part(dt_obj, country)

        st += "}}\n"

        text += st

        text = text + self.get_tech_templates(filename, geo_dict, country)
        if rail:
            text += "[[Category:Railway photographs taken on " + \
                dt_obj.strftime("%Y-%m-%d")+"]]" + "\n"
            if isinstance(country, str) and len(country) > 3:
                text += "[[Category:" + \
                    dt_obj.strftime("%B %Y") + \
                    " in rail transport in "+country+"]]" + "\n"

        text = text + "[[Category:" + wd_record["commons"] + "]]" + "\n"

        return {"name": commons_filename, "text": text, "dt_obj": dt_obj}

    def make_image_texts_simple(
        self, filename, wikidata, country='', photographer='Artem Svetlov', rail='', secondary_wikidata_ids=list()
    ) -> dict:
        # return file description texts
        # there is no excact 'city' in wikidata, use manual input cityname

        from model_wiki import Model_wiki  as Model_wiki_ask
        modelwiki = Model_wiki_ask()
    
        assert os.path.isfile(filename), 'not found '+filename

        # obtain exif
        dt_obj = self.image2datetime(filename)
        geo_dict = self.image2coords(filename)

        wd_record = modelwiki.get_wikidata_simplified(wikidata)

        instance_of_data = list()
        if 'instance_of_list' in wd_record:
            for i in wd_record['instance_of_list']:
                instance_of_data.append(
                    modelwiki.get_wikidata_simplified(i['value']))

        text = ""
        objectnames = {}

        objectnames['en'] = wd_record['names']["en"]
        objectnames['ru'] = wd_record['names']["ru"]
        for lang in self.optional_langs:
            if lang in wd_record['names']:
                objectnames[lang] = wd_record['names'][lang]


        objectname_long_ru = objectnames['ru']
        objectname_long_en = objectnames['en']
        # TODO change objectname_long_en to objectnames_long[en]
        objectnames_long = {}
        if len(instance_of_data) > 0:
            objectname_long_ru = ', '.join(
                d['names']['ru'] for d in instance_of_data) + ' '+objectnames['ru']
            objectname_long_en = ', '.join(
                d['names']['en'] for d in instance_of_data) + ' '+objectnames['en']
            for lang in self.optional_langs:
                try:
                    objectnames_long[lang] = ', '.join(
                        d['names'][lang] for d in instance_of_data) + ' '+objectnames[lang]
                except:
                    pass


        prototype = """== {{int:filedesc}} ==
{{Information
|description={{en|1=2nd Baumanskaya Street 1 k1}}{{ru|1=Вторая Бауманская улица дом 1 К1}} {{ on Wikidata|Q86663303}}  {{Building address|Country=RU|Street name=2-я Бауманская улица|House number=1 К1}}  
|source={{own}}
|author={{Creator:Artem Svetlov}}
|date={{According to Exif data|2022-07-03|location=Moscow}}
}}

{{Location|55.769326012498155|37.68742327500131}}
{{Taken with|Pentax K10D|sf=1|own=1}}

{{Photo Information
 |Model                 = Olympus mju II
 |ISO                   = 200
 |Lens                  = 
 |Focal length          = 35
 |Focal length 35mm     = 35
 |Support               = freehand
 |Film                  = Kodak Gold 200
 |Developer             = C41
 }}
 
    == {{int:license-header}} ==
    {{self|cc-by-sa-4.0|author=Артём Светлов}}

    [[Category:2nd Baumanskaya Street 1 k1]]
    [[Category:Photographs by Artem Svetlov/Moscow]]

    """
        st = """== {{int:filedesc}} ==
{{Information
|description="""
        st += "{{en|1=" + objectname_long_en + "}} \n"
        st += "{{ru|1=" + objectname_long_ru + "}} \n"
        for lang in self.optional_langs:
            if lang in objectnames_long:
                st += "{{"+lang+"|1=" + objectnames_long[lang] + "}} \n"
        heritage_id = None
        heritage_id = self.get_heritage_id(wikidata)
        if heritage_id is not None:
            st += "{{Cultural Heritage Russia|" + heritage_id + "}}"
        st += " {{ on Wikidata|" + wikidata + "}}"
        st += "\n"
        st += self.get_date_information_part(dt_obj, country)

        st += "}}\n"

        text += st

        text = text + self.get_tech_templates(filename, geo_dict, country)
        if rail:
            text += "[[Category:Railway photographs taken on " + \
                dt_obj.strftime("%Y-%m-%d")+"]]" + "\n"
            if isinstance(country, str) and len(country) > 3:
                text += "[[Category:" + \
                    dt_obj.strftime("%B %Y") + \
                    " in rail transport in "+country+"]]" + "\n"

        #from model_wiki import Model_wiki  as Model_wiki_ask
        #modelwiki = Model_wiki_ask()
        if len(secondary_wikidata_ids)<1:
            text = text + "[[Category:" + wd_record["commons"] + "]]" + "\n"
        else:
            text = text + "[[Category:" + wd_record["commons"] + "]]" + "\n"
            for wdid in secondary_wikidata_ids:
                cat = modelwiki.get_category_object_in_location(wdid,wikidata,verbose=True)
                if cat is not None: 
                    text = text + cat + "\n"
                else:
                    wd_record = modelwiki.get_wikidata_simplified(wdid)
                    
                    assert 'commons' in wd_record, 'https://www.wikidata.org/wiki/'+wdid + ' must have commons'
                    text = text + "[[Category:" + wd_record["commons"] + "]]" + "\n"
        
        # file name on commons
        filename_base = os.path.splitext(os.path.basename(filename))[0]
        filename_extension = os.path.splitext(os.path.basename(filename))[1]
        commons_filename = (
            objectnames['en'] + " " +
            dt_obj.strftime("%Y-%m %s") + filename_extension
        )
        commons_filename = commons_filename.replace("/", " drob ")
        
        # add district name to file name
        try:
            administrative_name = modelwiki.get_wd_by_wdid(modelwiki.get_upper_location_wdid(modelwiki.get_wd_by_wdid(wikidata)))['labels']['en']
            commons_filename = administrative_name + '_'+commons_filename
        except:
            pass
        
        return {"name": commons_filename, "text": text, "dt_obj": dt_obj}


    def take_user_wikidata_id(self, wdid) -> str:
        warnings.warn('moved to model_wiki', DeprecationWarning, stacklevel=2)
        # parse user input wikidata string.
        # it may be wikidata id, wikidata uri, string.
        # call search if need
        # return valid wikidata id
        if self.is_wikidata_id(wdid):
            result_wdid = wdid
        else:
            result_wdid = self.search_wikidata_by_string(
                wdid, stop_on_error=True)

        return result_wdid

    def get_shutterstock_desc(self, wikidata_list, filename, city, date=None) -> str:
        # https://support.submit.shutterstock.com/s/article/How-do-I-include-metadata-with-my-content?language=en_US
        '''
        Column A: Filename
Column B: Description
Column C: Keywords (separated by commas)
Column D: Categories ( 1 or 2, separated by commas, must be selected from this list)
Column E*: Illustration (Yes or No)
Column F*: Mature Content (Yes or No)
Column G*: Editorial (Yes or No)

he Illustration , Mature Content, and Editorial tags are optional and can be included or excluded from your CSV 
 Think of your title as a news headline and try to answer the main questions of: Who, What, When, Where, and Why. Be descriptive and use words that capture the emotion or mood of the image.
 Keywords must be in English, however, exceptions are made for scientific Latin names of plants and animals, names of places, and foreign terms or phrases commonly used in the English language.


Kaliningrad, Russia - August 28 2021: Tram car Tatra KT4 in city streets, in red color


        '''
        desc = {
            'Filename': filename,
            'Description': '',
            'Keywords': '',
            'Categories': '',
            'Editorial': 'Yes',
        }
        keywords = list()

        objects_wikidata = list()
        for obj_wdid in wikidata_list:
            obj_wdid = self.take_user_wikidata_id(obj_wdid)
            obj_wd = self.get_wikidata(obj_wdid)
            objects_wikidata.append(obj_wd)

        if self.is_wikidata_id(city):
            city_wdid = city
        else:
            city_wdid = self.search_wikidata_by_string(
                city, stop_on_error=True)
        city_wd = self.get_wikidata(city_wdid)

        # get country, only actual values. key --all returns historical values
        cmd = ['wd', 'claims', city_wdid, 'P17', '--json']
        response = subprocess.run(cmd, capture_output=True)
        country_json = json.loads(response.stdout.decode())
        country_wdid = country_json[0]
        country_wd = self.get_wikidata(country_wdid)

        try:
            dt_obj = self.image2datetime(filename)
        except:
            assert date is not None,'in image '+filename+'date can not be read from exif, need set date in --date yyyy-mm-dd'
            dt_obj = datetime.strptime(date, "%Y-%m-%d")
            
        object_captions = list()
        for obj_wd in objects_wikidata:
            object_captions.append(obj_wd['labels']['en'])

        d = '{city}, {country} - {date}: {caption}'.format(
            city=city_wd['labels']['en'],
            country=country_wd["labels"]["en"],
            date=dt_obj.strftime("%B %-d %Y"),
            caption=' '.join(object_captions)
        )

        for obj_wd in objects_wikidata:
            keywords.append(obj_wd['labels']['en'])
            aliases = obj_wd['aliases'].get('en',None)
            if type(aliases) == list and len(aliases)>0:
                keywords+=aliases

        keywords.append(city_wd['labels']['en'])
        keywords.append(city_wd['labels']['ru'])
        keywords.append(country_wd["labels"]["ru"])

        return d, keywords

    def get_camera_text(self, filename) -> str:
        st = ''
        image_exif = self.image2camera_params(filename)
        if image_exif.get("make") is not None and image_exif.get("model") is not None:
            if image_exif.get("make") != "" and image_exif.get("model") != "":
                make = image_exif.get("make").strip()
                model = image_exif.get("model").strip()
                make = make.capitalize()
                st = "{{Taken with|" + make + " " + model + "|sf=1|own=1}}" + "\n"


                
                st += '{{Photo Information|Model = ' + make + " " + model
                if image_exif.get("lensmodel", '') != "" and image_exif.get("lensmodel", '') != "":
                    st += '|Lens = ' + image_exif.get("lensmodel")
                    #if image_exif.get("lensmodel") == 'A Series Lens':
                    #    self.pp.pprint(image_exif)
                    #    quit()
                if image_exif.get("fnumber", '') != "" and image_exif.get("fnumber", '') != "":
                    st += '|Aperture = f/' + str(image_exif.get("fnumber"))
                if image_exif.get("'focallengthin35mmformat'", '') != "" and image_exif.get("'focallengthin35mmformat'", '') != "":
                    st += '|Focal length 35mm = f/' + \
                        str(image_exif.get("'focallengthin35mmformat'"))
                st += '}}' + "\n"

                cameramodels_dict = {
                    'Pentax corporation PENTAX K10D': 'Pentax K10D',
                    'Gopro HERO8 Black': 'GoPro Hero8 Black',
                    'Samsung SM-G7810': 'Samsung Galaxy S20 FE 5G',
                    'Olympus imaging corp.': 'Olympus',
                    'Nikon corporation NIKON': 'Nikon',
                    'Panasonic': 'Panasonic Lumix',
                    'Hmd global Nokia 5.3': 'Nokia 5.3',
                }
                lensmodel_dict = {
                    'OLYMPUS M.12-40mm F2.8': 'Olympus M.Zuiko Digital ED 12-40mm f/2.8 PRO',
                    'smc PENTAX-DA 35mm F2.4 AL':'SMC Pentax-DA 35mm F2.4',
                    'smc PENTAX-DA 14mm F2.8 EDIF':'SMC PENTAX DA 14 mm f/2.8 ED IF',
                }
                for camerastring in cameramodels_dict.keys():
                    if camerastring in st:
                        st = st.replace(
                            camerastring, cameramodels_dict[camerastring])

                if image_exif.get("lensmodel", '') != "" and image_exif.get("lensmodel", '') != "":
                    st += "{{Taken with|" + image_exif.get("lensmodel").replace(
                        '[', '').replace(']', '').replace('f/ ', 'f/') + "|sf=1|own=1}}" + "\n"

                for lensstring in lensmodel_dict.keys():
                    if lensstring in st:
                        st = st.replace(lensstring, lensmodel_dict[lensstring])
                
                st = st.replace('Canon Canon','Canon')

                return st
        else:
            return ''

    def image2camera_params_0(self, path):
        with open(path, "rb") as image_file:
            image_exif = Image(image_file)
        return image_exif

    def image2camera_params(self, path):
        try:
            with exiftool.ExifToolHelper() as et:
                metadata = et.get_metadata(path)
            metadata = metadata[0]

            new_metadata = dict()
            for k, v in metadata.items():
                if ':' not in k:
                    continue
                new_metadata[k.split(':')[1].lower()] = v
            metadata = new_metadata
            return metadata
        except:
            self.logger.info(
                'error while call python exifread. Try get EXIF by call exifread executable')

            cmd = [self.exiftool_path, path, '-json', '-n']
            response = subprocess.run(cmd, capture_output=True)
            metadata = json.loads(response.stdout.decode())

            metadata = metadata[0]

            new_metadata = dict()
            for k, v in metadata.items():
                new_metadata[k.lower()] = v
            metadata = new_metadata

            return metadata

    def check_exif_valid(self, path):

        cmd = [self.exiftool_path, path, "-datetimeoriginal", "-csv"]
        process = subprocess.run(cmd)

        if process.returncode == 0:
            return True
        else:
            return False

    def image2datetime(self, path):

        with open(path, "rb") as image_file:
            try:
                image_exif = Image(image_file)

                dt_str = image_exif.get("datetime_original", None)
                dt_obj = datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
            except:
                dt_obj = None
                cmd = [self.exiftool_path, path, "-datetimeoriginal", "-csv"]
                exiftool_text_result = subprocess.check_output(cmd)
                tmp = exiftool_text_result.splitlines()[1].split(b",")
                if len(tmp) > 1:
                    dt_str = tmp[1]
                    dt_obj = datetime.strptime(
                        dt_str.decode("UTF-8"), "%Y:%m:%d %H:%M:%S"
                    )

            if dt_obj is None:
                dt_obj = datetime.strptime(os.path.basename(path)[
                                           0:15], '%Y%m%d_%H%M%S')

            if dt_obj is None:
                return None
            return dt_obj

    def image2coords(self, path):
        exiftool_metadata = self.image2camera_params(path)
        try:
            lat = round(float(exiftool_metadata.get('gpslatitude')), 6)
            lon = round(float(exiftool_metadata.get('gpslongitude')), 6)
        except:
            self.logger.warning('no coordinates in '+path)
            return None

        geo_dict = {}
        geo_dict = {"lat": lat, "lon": lon}
        if 'gpsimgdirection' in exiftool_metadata:
            geo_dict["direction"] = round(
                float(exiftool_metadata.get('gpsimgdirection')))

        if 'gpsdestlatitude' in exiftool_metadata:
            geo_dict["dest_lat"] = round(
                float(exiftool_metadata.get('gpslatitude')), 6)
        if 'gpsdestlongitude' in exiftool_metadata:
            geo_dict["dest_lon"] = round(
                float(exiftool_metadata.get('gpsdestlongitude')), 6)

        return geo_dict

    def image2coords0(self, path):
        def dms_to_dd(d, m, s):
            dd = d + float(m) / 60 + float(s) / 3600
            return dd

        try:
            with open(path, "rb") as image_file:
                image_exif = Image(image_file)
                lat_dms = image_exif.gps_latitude
                lat = dms_to_dd(lat_dms[0], lat_dms[1], lat_dms[2])
                lon_dms = image_exif.gps_longitude
                lon = dms_to_dd(lon_dms[0], lon_dms[1], lon_dms[2])

                lat = round(float(lat), 6)
                lon = round(float(lon), 6)

                direction = None
                if "gps_img_direction" in image_exif.list_all():
                    try:
                        direction = round(float(image_exif.gps_img_direction))
                    except:
                        direction = None
                geo_dict = {}
                geo_dict = {"lat": lat, "lon": lon}
                if direction:
                    geo_dict["direction"] = direction

                # dest coords

                dest_lat = None
                dest_lon = None
                try:
                    lat_dms = image_exif.gps_dest_latitude
                    lat = dms_to_dd(lat_dms[0], lat_dms[1], lat_dms[2])
                    lon_dms = image_exif.gps_dest_longitude
                    lon = dms_to_dd(lon_dms[0], lon_dms[1], lon_dms[2])

                    dest_lat = round(float(lat), 6)
                    dest_lon = round(float(lon), 6)
                except:
                    pass
                if dest_lat is not None:
                    geo_dict["dest_lat"] = dest_lat
                    geo_dict["dest_lon"] = dest_lon

                return geo_dict

        except:
            return None

    def prepare_commonsfilename(self, commonsfilename):
        commonsfilename = commonsfilename.strip()
        if commonsfilename.startswith("File:") == False:
            commonsfilename = "File:" + commonsfilename
        commonsfilename = commonsfilename.replace("_", " ")
        return commonsfilename

    def write_iptc(self, path, caption, keywords):
        # path can be both filename or directory
        assert os.path.exists(path)
        
        '''
        To prevent duplication when adding new items, specific items can be deleted then added back again in the same command. For example, the following command adds the keywords "one" and "two", ensuring that they are not duplicated if they already existed in the keywords of an image:

exiftool -keywords-=one -keywords+=one -keywords-=two -keywords+=two DIR
        '''
        
        #workaround for write utf-8 keywords: write them to file
        argfiletext = ''
        if isinstance(keywords, list) and len(keywords) > 0:
            for keyword in keywords:
                argfiletext += '-keywords-='+keyword+''+" \n"+'-keywords+='+keyword+' '+"\n"
                
        argfile = tempfile.NamedTemporaryFile()
        argfilename = 't.txt'
        with open(argfilename, 'w') as f:
            f.write(argfiletext)
        
        cmd = [self.exiftool_path, '-preserve', '-overwrite_original', '-charset iptc=UTF8', '-charset', 'utf8', '-codedcharacterset=utf8',
        '-@', argfilename, path]
        print(' '.join(cmd))
        response = subprocess.run(cmd, capture_output=True)
        
        if isinstance(caption, str):
            cmd = [self.exiftool_path, '-preserve', '-overwrite_original',
                   '-Caption-Abstract='+caption+'', path]
            response = subprocess.run(cmd, capture_output=True)

    def print_structured_data(self, commonsfilename):
        warnings.warn('moved to model_wiki', DeprecationWarning, stacklevel=2)
        commonsfilename = self.prepare_commonsfilename(commonsfilename)
        commons_site = pywikibot.Site("commons", "commons")

        # File to test and work with

        page = pywikibot.FilePage(commons_site, commonsfilename)

        # Retrieve Wikibase data
        item = page.data_item()
        item.get()

        print("Commons MID:", item.id)  # M56723871

        for prop in item.claims:
            for statement in item.claims[prop]:
                if isinstance(statement.target, pywikibot.page._wikibase.ItemPage):
                    print(prop, statement.target.id,
                          statement.target.labels.get("en"))
                else:
                    print(prop, statement.target)

    def get_heritage_id(self, wikidata) -> str:
        warnings.warn('moved to model_wiki', DeprecationWarning, stacklevel=2)
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

    def append_structured_data0(self, commonsfilename):
        commonsfilename = self.prepare_commonsfilename(commonsfilename)
        commons_site = pywikibot.Site("commons", "commons")

        # File to test and work with

        page = pywikibot.FilePage(commons_site, commonsfilename)
        repo = commons_site.data_repository()

        # Retrieve Wikibase data
        item = page.data_item()
        item.get()

        print("Commons MID:", item.id)  # M56723871

        stringclaim = pywikibot.Claim(repo, "P180")  # Adding IMDb ID (P345)
        stringclaim.setTarget(4212644)  # Using a string
        item.addClaim(stringclaim, summary="Adding string claim")

    def append_image_descripts_claim(self, commonsfilename, entity_list, dry_run):
        warnings.warn('moved to model_wiki', DeprecationWarning, stacklevel=2)
        assert isinstance(entity_list, list)
        assert len(entity_list) > 0
        if dry_run:
            print('simulate add entities')
            self.pp.pprint(entity_list)
            return
        commonsfilename = self.prepare_commonsfilename(commonsfilename)

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
                
    def commons2stock_dev(self,url,city_wdid,images_dir = 'stocks', dry_run=False, date=None):
        
        site = pywikibot.Site('commons', 'commons')
        file_page = pywikibot.FilePage(site,url.replace('https://commons.wikimedia.org/wiki/',''))
        
        data_item = file_page.data_item()
        data_item.get()
        
        wd_ids = list()

        for prop in data_item.claims:
            if prop != 'P180': continue
            for statement in data_item.claims[prop]:
                if isinstance(statement.target, pywikibot.page._wikibase.ItemPage):
                    print(prop, statement.target.id)
                    wd_ids.append(statement.target.id)
        
        if not os.path.isdir(images_dir):
            os.makedirs(images_dir)
        filename = os.path.join(images_dir,url.replace('https://commons.wikimedia.org/wiki/File:',''))
        if not os.path.exists(filename):
            self.logger.debug('download: '+filename)
            file_page.download(filename)
        
        caption, keywords = self.get_shutterstock_desc(
        filename=filename,
        wikidata_list=wd_ids,
        city=city_wdid,
        date = date,
        )
        
        if dry_run:
            print()
            print(filename)
            print(caption)
            print(', '.join(keywords))
            return

        self.write_iptc(filename, caption, keywords)
        #processed_files.append(filename)
