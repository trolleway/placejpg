import pywikibot
import json

from exif import Image
import exiftool
import locale

from PIL import Image as PILImage

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
import shutil
from tqdm import tqdm

import contextlib
import io

import placejpgconfig
from iptcinfo3 import IPTCInfo


class Fileprocessor:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger(__name__)
    pp = pprint.PrettyPrinter(indent=4)

    langs_optional = placejpgconfig.langs_optional
    langs_primary = placejpgconfig.langs_primary
    
    exiftool_path = "exiftool"
    
    # TIFF LARGER THAN THIS VALUE WILL BE COMPRESSED TO WEBP 
    tiff2webp_min_size_mb = 19
    
    # Size of chunk for all uploads to wikimedia engine
    chunk_size = 10240000
    
    photographer = placejpgconfig.photographer
    folder_keywords = ['commons_uploaded', 'commons_duplicates']
    wikidata_cache = dict()

    def convert_to_webp(self, filepath: str) -> str:
        """Convert image to webp.

        Args:
            source (pathlib.Path): Path to source image

        Returns:
            pathlib.Path: path to new image
        """
        destination = os.path.splitext(filepath)[0]+'.webp'

        image = PILImage.open(filepath)  # Open image
        image.save(destination, format="webp", lossless=False,
                   quality=98)  # Convert image to webp

        # copy metadata to webp require recent exiftool
        try:
            subprocess.check_output(["exiftool", "-ver"])
            cmd = ['exiftool', '-charset', 'utf8', '-tagsfromfile',
               filepath, '-overwrite_original',  destination]  # '-all:all' ,
            subprocess.run(cmd)
        except subprocess.CalledProcessError:
            print("Exiftool is not installed. WEBP file created without exif tags")

        return destination

    def input2filelist(self, filepath,mode=None):
        if os.path.isfile(filepath):
            files = [filepath]
            assert os.path.isfile(filepath)
            uploaded_folder_path = os.path.join(
                os.path.dirname(filepath), 'commons_uploaded')
        elif os.path.isdir(filepath):
            files = os.listdir(filepath)
            files = [os.path.join(filepath, x) for x in files]
            folder_keywords = self.folder_keywords
            if mode=='replace_duplicates':
                while 'commons_duplicates' in folder_keywords: folder_keywords.remove('commons_duplicates') 
            files = list(
                filter(lambda name: not any(keyword in name for keyword in folder_keywords), files))

            uploaded_folder_path = os.path.join(filepath, 'commons_uploaded')
        else:
            raise Exception("filepath should be file or directory")
        return files, uploaded_folder_path

    def prepare_wikidata_url(self, wikidata) -> str:
        # convert string https://www.wikidata.org/wiki/Q4412648 to Q4412648

        wikidata = str(wikidata).strip()
        wikidata = wikidata.replace('https://www.wikidata.org/wiki/', '')

        return wikidata

    def upload_file(self, filepath, commons_name, description, verify_description=False,ignore_warning=False):
        # The site object for Wikimedia Commons
        site = pywikibot.Site("commons", "commons")
        logging.basicConfig(level=logging.DEBUG, format='%(message)s')

        # The upload robot object
        bot = UploadRobot(
            [filepath],  # A list of files to upload
            description=description,  # The description of the file
            # keep original names of urls and files, otherwise it will ask to enter a name for each file
            use_filename=commons_name,
            keep_filename=True,  # Keep the filename as is
            # Ask for verification of the description
            verify_description=verify_description,
            targetSite=site,  # The site object for Wikimedia Commons
            aborts=True,  # List of the warning types to abort upload on
            chunk_size=self.chunk_size,
            summary='Upload with placejpg',
            ignore_warning=ignore_warning
        )
        print()
        print('=======================================================')
        print(commons_name.center(60, '*'))
        # Try to run the upload robot
        try:
            # bot.run()
            # SAVE pywikibot screen output to move photos to subdirs by errors
            f = io.StringIO()
            with contextlib.redirect_stderr(f):
                bot.run()
            pywikibot_output = f.getvalue()
            # print('>>>'+pywikibot_output+'<<<')
            return pywikibot_output
        except Exception as e:
            # Handle API errors
            print(f"API error: {e.code}: {e.info}")
            return False
        return None

    def deprecated_get_wikidata_simplified(self, wikidata) -> dict:
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
            raise ValueError('object https://www.wikidata.org/wiki/' +
                             wikidata+' must has name ru and name en')

        for lang in self.langs_optional:
            if lang in object_wd["labels"]:
                object_record['names'][lang] = object_wd["labels"][lang]
        if "P373" in object_wd["claims"]:
            object_record['commons'] = object_wd["claims"]["P373"][0]["value"]
        elif 'commonswiki' in object_wd["sitelinks"]:
            object_record['commons'] = object_wd["sitelinks"]["commonswiki"]["title"].replace(
                'Category:', '')
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
    
    def get_place_from_input(self,filename:str,street:str,geo_dict:dict,override_key='placeQ',geodata_attribute='wikidata',layer=None)->str:
            '''
            return wikidata id of photo place
            diffirent input variants accepted:

            * upload-vehicle.py --street Q12345678 EP2D-0030.jpg
                    return Q12345678
            * upload-vehicle.py --street rail.gpkg EP2D-0030.jpg
                    read coordinates from EXIF, search by coordinates in rail.gpkg
                    open 1st layer in vector file, get 'wikidata' field value
            * upload-vehicle.py --street rail.gpkg EP2D-0030_placeQ12345678.jpg 
                    return Q12345678
            
            '''
            from model_wiki import Model_wiki as Model_wiki_ask
            modelwiki = Model_wiki_ask()
            
            # take place from filename if present
            if os.path.basename(filename).find(override_key)>0:
                places=street_wdid = self.get_placewikidatalist_from_string(
                    os.path.basename(filename))
                print(places)
                street_wdid =  places[0]
                del places
            elif os.path.isfile(street):
                if geo_dict is None:
                    self.logger.error(
                        filename + '  must have coordinates for search in geodata, or set --street')
                    return None
                regions_filepath = street
                from model_geo import Model_Geo as Model_geo_ask
                modelgeo = Model_geo_ask()
                if 'dest_lat' in geo_dict and 'dest_lon' in geo_dict:
                    lat=geo_dict.get("dest_lat")
                    lon=geo_dict.get("dest_lon")
                else:
                    lat=geo_dict.get("lat")
                    lon=geo_dict.get("lon")
                street_wdid = modelgeo.identify_deodata(lat, lon, regions_filepath, layer=layer, fieldname=geodata_attribute)
                if street_wdid is None:
                    msg = f'file:{regions_filepath} https://geohack.toolforge.org/geohack.php?params={lat};{lon}_type:camera'
                    self.logger.error(filename.ljust(
                        40) + ' no found '+msg+'')
                    modelgeo.save_not_found_geom(lat,lon,filename)
                    return None
                #street_wd = modelwiki.get_wikidata_simplified(street_wdid)
            else:
                # take street from user input

                street_wdid = modelwiki.wikidata_input2id(street)
                if street is not None:
                    assert street_wdid is not None
            return street_wdid

    def get_coordinate_from_string(self,filename)->list:
        # COORDINATE
        # search filename for pattern "LatLng(55.59818, 37.58834)"
        import re
        l=None
        regex = "_LatLng(.*?)[)]"
        test_str = os.path.basename(filename)

        matches = re.finditer(regex, test_str, re.MULTILINE)
        for match in matches:
            l = match.group()[len('_LatLng('):-1]
            parts=l.split(',')
            lat=float(parts[0].strip())
            lon=float(parts[1].strip())
            
            return lat,lon
        
        return None,None

    def make_image_texts_vehicle(self, filename, vehicle, model=None, number=None, street=None, system=None,  route=None, country=None, line=None, facing=None, colors=None, operator=None, operator_vehicle_category=None, secondary_wikidata_ids=None, digital_number=None, custom_categories=list(), suffix='', skip_unixtime=False) -> dict:
        assert os.path.isfile(filename)


        from model_wiki import Model_wiki as Model_wiki_ask
        modelwiki = Model_wiki_ask()
        categories = set()
        need_create_categories = list()
        location_of_creation = ''

        vehicle_names = {'ru': {'tram': 'трамвай', 'trolleybus': 'троллейбус',
                                'bus': 'автобус', 'train': 'поезд', 'locomotive': 'локомотив', 'auto': 'автомобиль', 'plane': 'самолёт','metro':'метропоезд'}}
        wikidata_4_structured_data = set()
        if secondary_wikidata_ids is None: secondary_wikidata_ids = list()
        train_synonims = ['train', 'locomotive', 'emu', 'dmu','metro']

        # assert facing in ('Left','Right',None)

        # obtain exif
        dt_obj = self.image2datetime(filename)
        geo_dict = self.image2coords(filename)



        # STREET
        # if street - vector file path: get street wikidata code by point in polygon
        if street is not None:
            street_wdid = self.get_place_from_input(filename,street,geo_dict)
            
            if street_wdid is None:
                self.logger.error('not set place/street')
                return None
            street_wd = modelwiki.get_wikidata_simplified(street_wdid)
            street_names = street_wd["labels"]
            wikidata_4_structured_data.add(street_wd['id'])
            # add city/district to structured data
            city_wd = modelwiki.get_territorial_entity(street_wd)
            if city_wd is None:
                msg = 'https://www.wikidata.org/wiki/' + \
                    str(street_wdid) + ' must have territorial entity'
                self.logger.error(msg)
                return None

            wikidata_4_structured_data.add(city_wd['id'])
        
        # Optionaly obtain country from gpkg file if country parameter is path to vector file (.gpkg)
        if os.path.isfile(country):
            country = self.get_place_from_input(filename,country,geo_dict,override_key='_location',geodata_attribute='name:en')
            if country is None:
                #place should taken from gpkg, but not found
                return None  

                 


        
        # TAKEN ON LOCATION
        # search filename for pattern "_locationMoscow-Oblast"
        import re
        l=None
        regex = "_location(.*?)[_.\b]"
        test_str = os.path.basename(filename)

        matches = re.finditer(regex, test_str, re.MULTILINE)
        for match in matches:
            l = match.group()[9:-1].replace('-',' ').title()
        if l == 'location':
            l = None
        if l is not None: country=l
        del l
        
        # MODEL 
        if model is None:
            # extract model "Q123456" from 16666_20070707_000_modelQ123456.jpg
            import re
            regex = "_model(.*?)[_.\b]"
            test_str = os.path.basename(filename)

            matches = re.finditer(regex, test_str, re.MULTILINE)
            for match in matches:
                model = match.group()[6:-1]
                
        if model is not None:
            model_wdid = modelwiki.wikidata_input2id(model)
            model_wd = modelwiki.get_wikidata_simplified(model_wdid)
            model_names = model_wd["labels"]
            wikidata_4_structured_data.add(model_wd['id'])

        # ROUTE
        if route is None:
            # extract route "34" from 3216_20070112_052_r34.jpg
            import re
            regex = "_r(.*?)[_.\b]"
            test_str = os.path.basename(filename)

            matches = re.finditer(regex, test_str, re.MULTILINE)
            for match in matches:
                result = match.group()[2:-1]
                if 'eplace' in result:
                    continue
                route = result
                del result
            if route == 'z':
                route = None

        # DIGITAL_NUMBER
        if digital_number is None:
            # extract number "1456" from 2TE10M-1456_20230122_444_dn1456.jpg
            import re
            regex = "_n(.*?)[_.\b]"
            test_str = os.path.basename(filename)

            matches = re.finditer(regex, test_str, re.MULTILINE)
            for match in matches:
                digital_number = match.group()[2:-1]
        
        # LICENSE PLATE
        license_plate=''
        license_plate=self.get_licenceplate_from_string(filename)

        # OPERATOR
        if operator is not None:

            operator_wd = modelwiki.get_wikidata_simplified(modelwiki.wikidata_input2id(operator))
            wikidata_4_structured_data.add(operator_wd['id'])
        # OPERATOR VEHICLE CATEGORY
        if operator_vehicle_category is not None:
            categories.add(operator_vehicle_category.replace('Category:',''))


        # SYSTEM
        if system=='FROMFILENAME':
            # extract system "Q123456" from 16666_20070707_000_systemQ123456.jpg
            import re
            regex = "_system(.*?)[_.\b]"
            test_str = os.path.basename(filename)

            matches = re.finditer(regex, test_str, re.MULTILINE)
            for match in matches:
                system = match.group()[7:-1]
        system_names = dict()
        if system is not None:
            system_wdid = modelwiki.wikidata_input2id(system)
            system_wd = modelwiki.get_wikidata_simplified(system_wdid)

            system_names = system_wd["labels"]
            # GET "RZD" from "Russian Railways"
            if 'P1813' in system_wd['claims']:
                for abbr_record in system_wd['claims']['P1813']:
                    system_names[abbr_record['language']
                                 ] = abbr_record['value']

            wikidata_4_structured_data.add(system_wd['id'])
            system_territorial_entity = modelwiki.get_territorial_entity(
                system_wd)
            if system_territorial_entity is not None:
                city_name_en = system_territorial_entity['labels']['en'] or ''
                city_name_ru = system_territorial_entity['labels']['ru'] or ''
            else:
                city_name_en = None
                city_name_ru = None

        if system is None or (city_name_en is None or city_name_ru is None):
            city_wd = modelwiki.get_territorial_entity(street_wd)
            try:
                city_name_en = city_wd['labels']['en']
                city_name_ru = city_wd['labels']['ru']
            except:
                raise ValueError('object https://www.wikidata.org/wiki/' +
                                 city_wd['id']+' must has name ru and name en')
            if city_wd['id'] not in wikidata_4_structured_data:
                wikidata_4_structured_data.add(city_wd['id'])
        
        assert city_name_en is not None

        # LINE
        line_wdid = None
        line_wd = None
        line_names = dict()
        if line is not None:
            line_wdid = self.take_user_wikidata_id(line)
            line_wd = modelwiki.get_wikidata_simplified(line_wdid)

            line_names = line_wd["labels"]

            wikidata_4_structured_data.add(line_wdid)
        elif line is None and vehicle in train_synonims:
            # GET RAILWAY LINE FROM WIKIDATA
            if 'P81' in street_wd['claims'] and len(street_wd['claims']['P81']) == 1:
                line_wd = modelwiki.get_wikidata_simplified(
                    street_wd['claims']['P81'][0]['value'])
                line_wdid = line_wd['id']

        # trollybus garage numbers. extract 3213 from 3213_20060702_162.jpg
        if number == 'BEFORE_UNDERSCORE':
            number = os.path.basename(
                filename)[0:os.path.basename(filename).find('_')]

        filename_base = os.path.splitext(os.path.basename(filename))[0]
        filename_extension = os.path.splitext(os.path.basename(filename))[1]

        placenames = {'ru': list(), 'en': list()}

        if 'en' in line_names:
            if len(line_names['en']) > 0:
                placenames['en'].append(line_names['en'])
        if 'street_names' in locals() and 'en' in street_names:
            if street_names['en'] != '':
                placenames['en'].append(street_names['en'])
        
        if suffix != '':
            suffix=f' {suffix}'
        if skip_unixtime:
            timestamp_format=''
        else:
            timestamp_format='%s'


        if vehicle == 'auto' or (vehicle not in train_synonims and  number is None):
            if 'en' not in model_names:
                raise ValueError('vehicle model https://www.wikidata.org/wiki/' +
                             model_wdid+' must has name en')
            objectname_en = '{city} {transport} {license_plate}'.format(
                transport=vehicle,
                city=city_name_en,
                model=model_names['en'],
                license_plate=license_plate
            )

            objectname_ru = '{city}, {transport} {model} {license_plate}'.format(
                city=city_name_ru,
                transport=vehicle_names['ru'][vehicle],
                model=model_names.get('ru', model_names['en']),
                license_plate=license_plate
            )
            if license_plate != '':
                objectname_ru = ' '+objectname_ru
            
            if vehicle != 'auto':
                commons_filename = '{city} {transport} {license_plate} {dt} {timestamp} {place} {model}{suffix}{extension}'.format(
                    city=city_name_en,
                    transport=vehicle,
                    license_plate=license_plate,
                    dt=dt_obj.strftime("%Y-%m"),
                    timestamp = dt_obj.strftime(timestamp_format),
                    place=' '.join(placenames['en']),
                    model=model_names['en'],
                    suffix=suffix,
                    extension=filename_extension)
            elif vehicle == 'auto':
                commons_filename = '{transport} {model} {city} {place} {license_plate} {dt} {timestamp}{suffix}{extension}'.format(
                    city=city_name_en,
                    transport=vehicle,
                    license_plate=license_plate,
                    dt=dt_obj.strftime("%Y-%m"),
                    timestamp = dt_obj.strftime(timestamp_format),
                    place=' '.join(placenames['en']),
                    model=model_names['en'],
                    suffix=suffix,
                    extension=filename_extension)
            
        elif vehicle not in train_synonims:
            objectname_en = '{city} {transport} {number}'.format(
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
            if license_plate != '':
                objectname_ru = ' '+objectname_ru
            
            commons_filename = '{city} {transport} {number} {dt} {timestamp} {place} {model}{suffix}{extension}'.format(
                city=city_name_en,
                transport=vehicle,
                number=number,
                dt=dt_obj.strftime("%Y-%m"),
                timestamp = dt_obj.strftime(timestamp_format),
                place=' '.join(placenames['en']),
                model=model_names['en'],
                suffix=suffix,
                extension=filename_extension)

            # filename for Moscow Trolleybus
            if system_wdid == 'Q4304313':
                commons_filename = '{city} {transport} {model} {number} {dt} {place}{suffix}{extension}'.format(
                    city=city_name_en,
                    transport=vehicle,
                    number=number,
                    dt=dt_obj.strftime("%Y-%m"),
                    timestamp = dt_obj.strftime(timestamp_format),
                    place=' '.join(placenames['en']),
                    model=model_names['en'],
                    suffix=suffix,
                    extension=filename_extension)

            commons_filename = commons_filename.replace('  ',' ')
            
            
        elif vehicle in train_synonims:
            assert street_names is not None or line_names is not None
            if 'en' not in system_names:
                system_names['en'] = ''
            if 'ru' not in system_names:
                system_names['ru'] = ''

            # {model} removed
            number_lat = translit(number, "ru", reversed=True)

            objectname_en = '{system}{number_lat}'.format(
                system=system_names['en']+' ',
                city=city_name_en,
                model=model_names['en'],
                number_lat=number_lat,
                place=' '.join(placenames['en'])
            )
            commons_filename = '{system}{number_lat} {dt} {place} {timestamp}{suffix}{extension}'.format(
                system=system_names['en']+' ',
                number_lat=number_lat,
                dt=dt_obj.strftime("%Y-%m"),
                place=' '.join(placenames['en']),
                timestamp=dt_obj.strftime("%s"),
                suffix=suffix,
                extension=filename_extension
            )

            objectname_ru = '{system}{number}'.format(
                system=system_names['ru']+' ',
                transport=vehicle_names['ru'][vehicle],
                model=model_names.get('ru', model_names['en']),
                number=number
            )

            locomotive_inscription = number_lat
            locomotive_railway_code = system_names['en']

        commons_filename = commons_filename.replace("/", " drob ")

        text = ''

        if vehicle in ('bus','trolleybus','tram'):
            text = """== {{int:filedesc}} ==
    {{Bus-Information
    |description="""
        else:
            text = """== {{int:filedesc}} ==
    {{Information
    |description="""
        captions = dict()
        assert 'en' in street_names,  'https://www.wikidata.org/wiki/' + \
            street_wdid + ' must have english name'
        captions['en'] = objectname_en + ' at ' + street_names['en']
        if route is not None:
            captions['en'] += ' Line '+route
        if line_wdid is not None:
            assert 'en' in modelwiki.get_wikidata_simplified(line_wdid)[
                'labels'], 'object https://www.wikidata.org/wiki/' + line_wdid + ' must has name en'
            captions['en'] += ' ' + \
                modelwiki.get_wikidata_simplified(line_wdid)['labels']['en']
        text += "{{en|1=" + captions['en'] + '}}'+"\n"

        lang='ru'
        assert street_names.get(lang,'') != '', 'object https://www.wikidata.org/wiki/' + line_wdid + ' must has name'+lang
        captions[lang] = objectname_ru + ' на ' +  \
            street_names[lang].replace(
                'Улица', 'улица').replace('Проспект', 'проспект')
        if route is not None:
            captions[lang] += ' Маршрут '+route
        if line_wdid is not None:
            captions[lang] += ' ' + \
                modelwiki.get_wikidata_simplified(line_wdid)['labels'][lang]
        text += "{{"+lang+"|1=" + captions[lang] + '}}'+"\n"

        if vehicle in ('bus','trolleybus','tram'):
            text += " {{#property:P180|from=M{{PAGEID}} }} \n"
        else:
            if model is not None:
                text += " {{on Wikidata|" + model_wdid.split('#')[0] + "}}\n"
                    
            text += " {{on Wikidata|" + street_wdid + "}}\n"

        if type(secondary_wikidata_ids) == list and len(secondary_wikidata_ids) > 0:
            for wdid in secondary_wikidata_ids:
                if vehicle in ('bus','trolleybus','tram'):
                    pass
                else:
                    text += " {{on Wikidata|" + wdid + "}}\n"
                heritage_id = None
                heritage_id = modelwiki.get_heritage_id(wdid)
                if heritage_id is not None:
                    text += "{{Cultural Heritage Russia|" + heritage_id + "}}"
                    today = datetime.today()
                    if today.strftime('%Y-%m') == '2024-09':
                        text += "{{Wiki Loves Monuments 2024|ru}}"
        text += "\n"
        
        if vehicle in ('bus','trolleybus','tram') and model is not None:
            text += "|Body={{on Wikidata|" + model_wdid.split('#')[0] + "}}\n"        
        if vehicle in ('bus','trolleybus','tram') and model is not None:
            text += "|Place={{#invoke:Information|SDC_Location|icon=true}} {{#if:{{#property:P1071|from=M{{PAGEID}} }}|(<small>{{#invoke:PropertyChain|PropertyChain|qID={{#invoke:WikidataIB |followQid |props=P1071}}|pID=P131|endpID=P17}}</small>)}}\n"
        if vehicle in ('bus','trolleybus','tram') and operator is not None:
            text += "|Operator={{on Wikidata|" + operator_wd + "}}\n"


        if vehicle in ('bus','trolleybus','tram'):
            text += "|number_plate=\n"
            text += "|depot=\n"
            if number is not None:
                text += "|fleet_number="+str(number)+"\n"
            if license_plate != '':
                text += "|license_plate="+str(license_plate)+"\n"
            text += "|Chassis=\n"
            text += "|Model_Year=\n"
    
        text += self.get_date_information_part(dt_obj, country)
        text += self.get_source_information_part(filename)
        text += "}}\n"
        tech_description, tech_categories = self.get_tech_description(filename, geo_dict)
        assert None not in tech_categories, 'None value in '+str(tech_categories)
        text +=tech_description+"\n"
        categories.update(tech_categories)
        if 'catid' in filename:
            assert custom_categories is not None
        if custom_categories is not None:
            categories.update(custom_categories)
        

        

        transports = {
            'tram': 'Trams',
            'trolleybus': 'Trolleybuses',
            'bus': 'Buses',
            'train': 'Rail vehicles',
            'metro': 'Rail vehicles',
            'locomotive': 'Locomotives',
            'auto': 'Automobiles'
        }
        transports_color = {
            'tram': 'Trams',
            'trolleybus': 'Trolleybuses',
            'bus': 'Buses',
            'train': 'Rail vehicles',
            'metro': 'Rail vehicles',
            'locomotive': 'Rail vehicles',
            'auto': 'Automobiles'
        }
        transports_wikidata = {
            'tram': 'Q3407658',
            'trolleybus': 'Q5639',
            'bus': 'Q5638',
            'train': 'Q1414135',
            'subway':'Q1414135',
            'locomotive': 'Q93301',
            'auto': 'Q1420'
        
        
        }
        
        # CATEGORY FOR ROUTE

        if route is not None:
            cat="{transports} on route {route} in {city}".format(
                transports=transports[vehicle],
                route=route,
                city=city_name_en)
            cat_content='''
{{GeoGroup}}
[[Category:$vehicle routes designated $route|$city_name_en]]
[[Category:$transports in $city_name_en by route|$route]]'''
            cat_content=cat_content.replace('$vehicle',vehicle.title())
            cat_content=cat_content.replace('$route',route)
            cat_content=cat_content.replace('$transports',transports[vehicle])
            cat_content=cat_content.replace('$city_name_en',city_name_en)
            need_create_categories.append({'name':cat,'content':cat_content})
            categories.add(cat)
            
            cat = 'Category:$transports in $city_name_en by route'.replace('$transports',transports[vehicle]).replace('$city_name_en',city_name_en)
            cat_content='''
{{GeoGroup}}
[[Category:$transports in $city_name_en]]'''    
            cat_content=cat_content.replace('$vehicle',vehicle.title())
            cat_content=cat_content.replace('$route',route)
            cat_content=cat_content.replace('$transports',transports[vehicle])
            cat_content=cat_content.replace('$city_name_en',city_name_en)
            need_create_categories.append({'name':cat,'content':cat_content})
            
        
        # CATEGORY BY PHOTOGRAPHER

        cat = 'Photographs by {photographer}/{country}/{transport}'
        cat = cat.format(photographer=self.photographer,
                         country=country,
                         transport=transports[vehicle].lower().capitalize())
        categories.add(cat)
        cat_content='''{{Usercat}}
[[Category:Photographs_by_'''+self.photographer+'/'+country+''']]'''
        modelwiki.create_category(
                cat, cat_content)
        cat = 'Photographs by {photographer}/{country}'
        cat = cat.format(photographer=self.photographer,
                         country=country,
                         transport=transports[vehicle].lower().capitalize())
        cat_content='''{{Usercat}}
[[Category:Photographs_by_'''+self.photographer+''']]
[[Category:Photographs_of_'''+country+'''_by_photographer]]'''
        modelwiki.create_category(
                cat, cat_content)


        trains_on_line_cat = None
        trains_on_station_cat = None

        if vehicle in train_synonims:
            trains_on_station_cat = None
            trains_on_station_cat = modelwiki.search_commonscat_by_2_wikidata(
                street_wdid, 'Q870')
            if trains_on_station_cat is None:
                if street_wd['commons'] is not None:
                    cat = 'Category:Trains at '+street_wd['commons']
                    if modelwiki.is_category_exists(cat):
                        trains_on_station_cat = cat
                        del cat

            if line_wd is not None:
                trains_on_line_cat = modelwiki.search_commonscat_by_2_wikidata(
                    line_wdid, 'Q870')
                if trains_on_line_cat is None:
                    if line_wd['commons'] is not None:
                        cat = 'Category:Trains on '+line_wd['commons']
                        if modelwiki.is_category_exists(cat):
                            trains_on_line_cat = cat
                            del cat

            # TRAINS AT STATION
            if trains_on_station_cat is not None:
                categories.add(trains_on_station_cat)
                if line_wdid is not None:
                    wikidata_4_structured_data.add(line_wdid)
                wikidata_4_structured_data.add(street_wdid)
            # TRAINS ON LINE
            elif trains_on_line_cat is not None:
                categories.add(trains_on_line_cat)
                if line_wdid is not None:
                    wikidata_4_structured_data.add(line_wdid)
                wikidata_4_structured_data.add(street_wdid)
            if trains_on_station_cat is None:
                # STATION
                if street_wd['commons'] is None:
                    self.logger.error('https://www.wikidata.org/wiki/' +
                                      street_wd['id'] + ' must have commons category')
                    return None
                categories.add(street_wd['commons'])
                wikidata_4_structured_data.add(street_wdid)
                # LINE
                if line_wd is not None:
                    wikidata_4_structured_data.add(line_wd['id'])
                    if trains_on_line_cat is None and line_wd['commons'] is not None:
                        categories.add(line_wd['commons'])

        else:
            if line_wd is not None:
                if line_wd['commons'] is not None:
                    categories.add(line_wd['commons'])
            if street_wd is not None and 'commons' in street_wd:
                categories.add(street_wd['commons'])

        assert None not in wikidata_4_structured_data, 'empty value added to structured data set:' + \
            str(' '.join(list(wikidata_4_structured_data)))

        # locale.setlocale(locale.LC_ALL, 'en_GB')
        if vehicle == 'tram':
            catname = "Railway photographs taken on "+dt_obj.strftime("%Y-%m-%d")
            categories.add(catname)

        if vehicle in train_synonims:
            catname = "Railway photographs taken on " + \
                dt_obj.strftime("%Y-%m-%d")
            categories.add(catname)
            modelwiki.create_category(
                catname, '{{Railway photographs taken on navbox}}')
            if isinstance(country, str) and len(country) > 3:
                catname = dt_obj.strftime("%B %Y") + \
                    " in rail transport in "+country
                categories.add(catname)
                category_content = '{{GeoGroup|level=2}}{{railtransportmonth-country|'+dt_obj.strftime(
                    "%Y")[0:3]+'|'+dt_obj.strftime("%Y")[-1:]+'|'+dt_obj.strftime("%m")+'|'+country+'}}'
                modelwiki.create_category(catname, category_content)



        # FACING

        if facing is None and 'facing' in os.path.basename(filename):
            facing = self.get_facing_from_string(os.path.basename(filename))        
        # do not add facing category if this is interior
        if 'Q60998096' in secondary_wikidata_ids:
            facing = None
        if facing is not None:
            facing = facing.strip().capitalize()
            # assert facing.strip().upper() in ('LEFT','RIGHT')

            if facing == 'Left':
                text += "[[Category:"+transports[vehicle] + \
                    " facing " + facing.lower() + "]]\n"
            if facing == 'Right':
                text += "[[Category:"+transports[vehicle] + \
                    " facing " + facing.lower() + "]]\n"
            if facing == 'Side':
                text += "[[Category:Side views of " + \
                    transports[vehicle].lower()+"]]\n"
            if facing == 'Rear':
                text += "[[Category:Rear views of " + \
                    transports[vehicle].lower()+"]]\n"
            if facing == 'Front':
                text += "[[Category:Front views of " + \
                    transports[vehicle].lower()+"]]\n"
            if facing == 'Rear three-quarter'.capitalize():
                text += "[[Category:Rear three-quarter views of " + \
                    transports[vehicle].lower()+"]]\n"
            if facing == 'rtq'.capitalize():
                text += "[[Category:Rear three-quarter views of " + \
                    transports[vehicle].lower()+"]]\n"
            if facing == 'Three-quarter'.capitalize():
                text += "[[Category:Three-quarter views of " + \
                    transports[vehicle].lower()+"]]\n"
            if facing == 'Tq'.capitalize():
                text += "[[Category:Three-quarter views of " + \
                    transports[vehicle].lower()+"]]\n"

            if facing == 'Left':
                wikidata_4_structured_data.add('Q119570753')
            if facing == 'Right':
                wikidata_4_structured_data.add('Q119570670')
            if facing == 'Front':
                wikidata_4_structured_data.add('Q1972238')
        elif facing is None:
            self.logger.info('🤏 direction of vehicle skipped')
            
        # COLORS CATEGORY
        liveries_codes=dict()
        liveries_codes['RZDGREEN']='Russian railways green livery'
        liveries_codes['RZD']='Russian Railways livery'
        liveries_codes['NASHEPODMOSKOVIE']='Nashe Podmoskovie livery'
        if colors is None and 'color' in os.path.basename(filename):
            colors = self.get_colorlist_from_string(os.path.basename(filename))
        if colors is not None:
            colorname = ''
            if colors[0].upper() == 'RZDGREEN':
                text += "[[Category:{transports} in Russian railways green livery]]\n".format(
                    transports=transports_color[vehicle].capitalize(),
                    colorname=colorname)
            elif colors[0].upper() == 'RZD':
                text += "[[Category:{transports} in Russian Railways livery]]\n".format(
                    transports=transports_color[vehicle].capitalize(),
                    colorname=colorname)
            elif colors[0].upper() == 'NASHEPODMOSKOVIE':
                text += "[[Category:{transports} in Nashe Podmoskovie livery]]\n".format(
                    transports=transports_color[vehicle].capitalize(),
                    colorname=colorname)
            else:
                colors.sort()
                colorname = ' and '.join(colors)
                colorname = colorname.lower().capitalize()
                text += "[[Category:{colorname} {transports}]]\n".format(
                    transports=transports_color[vehicle].lower(),
                    colorname=colorname)
        elif colors is None:
            txt="liveries codes:\n"
            for key in liveries_codes:
                txt = txt + f"🎨 {key} > {liveries_codes[key]} \n"
            self.logger.info('🤏 colors of vehicle skipped')
            print(txt)
            del txt



        # number
        has_category_for_this_vehicle = False
        
        if number is not None and number.isdigit():
            number_filtered = number
            if '-' in number_filtered:
                number_filtered = number_filtered[number_filtered.index(
                    '-')+1:]
            if digital_number is None:
                digital_number = number_filtered
        if number is not None and vehicle in ('bus','trolleybus','tram'):
            cat = f'{city_name_en} {vehicle} {number}'
            self.logger.info('search if exist optional category '+cat)
            if modelwiki.is_category_exists(cat):
                has_category_for_this_vehicle = True
                categories.add(cat)
        elif number is not None and vehicle in train_synonims:
            # search for category for this railway locomotive
            cat = f'{locomotive_railway_code} {locomotive_inscription}'
            if modelwiki.is_category_exists(cat):
                has_category_for_this_vehicle = True
                categories.add(cat)
            elif  digital_number.isdigit():
                catname = "Number "+digital_number+" on rail vehicles"
                category_page_content = '{{NumbercategoryTrain|'+digital_number+'}}'
                modelwiki.create_category(catname, category_page_content)
                categories.add(catname)

                # upper category
                catname = 'Number '+digital_number+' on vehicles'
                category_page_content = '{{Numbercategory-vehicle|'+digital_number + \
                    '|vehicle|Number '+digital_number+' on objects|Vehicle}}'
                modelwiki.create_category(catname, category_page_content)

                # upper category
                catname = 'Number '+digital_number+' on objects'
                category_page_content = '{{Number on object|n='+digital_number+'}}'
                modelwiki.create_category(catname, category_page_content)
        # end of search category for this vehicle 
        
        if number is not None and vehicle == 'bus' and digital_number.isdigit():
            catname = f'Number {digital_number} on buses'
            if not has_category_for_this_vehicle: categories.add(catname)
            modelwiki.create_number_on_vehicles_category(vehicle='bus', number=digital_number)
        elif number is not None and vehicle == 'trolleybus' and digital_number.isdigit():
            catname = f'Number {digital_number} on trolleybuses'
            if not has_category_for_this_vehicle: categories.add(catname)
            modelwiki.create_number_on_vehicles_category(vehicle='trolleybus', number=digital_number)
        elif number is not None and vehicle == 'tram' and digital_number.isdigit():
            catname="Trams with fleet number "+digital_number
            if not has_category_for_this_vehicle: categories.add(catname)
            category_page_content = '{{' + \
                f'Numbercategory-vehicle-fleet number|{digital_number}|Trams|Number {digital_number} on trams'+'|image=}}'
            modelwiki.create_category(catname, category_page_content)
        elif number is not None and vehicle != 'tram':
            pass

        if dt_obj is not None and vehicle not in train_synonims:
            catname = "{transports} in {country} photographed in {year}".format(
                transports=transports[vehicle],
                country=country,
                year=dt_obj.strftime("%Y"),
            )
            text += "[[Category:"+catname+"]]\n"
            if vehicle == 'trolleybus':
                category_page_content = "[[Category:{transports} photographed in {year}]]\n[[Category:{transports} photographed in {year}]]".format(
                    transports=transports[vehicle],
                    country=country,
                    year=dt_obj.strftime("%Y"),
                )

                modelwiki.create_category(catname, category_page_content)
        
        # AUTOMOBILES IN LOCATION
        if vehicle == 'auto':
            cat = modelwiki.get_category_object_in_location(
                transports_wikidata[vehicle], street_wd['id'], order=None, verbose=True)
            categories.add(cat)

        # MODEL IN LOCATION

        model_in_location_found = False
        # if dt_obj is not None and vehicle == 'trolleybus':
        # category for model. search for category like "ZIU-9 in Moscow"
        if not has_category_for_this_vehicle:
            if vehicle == 'auto': #for automobiles not use number plate
                cat = modelwiki.get_category_object_in_location(
                    model_wd['id'], street_wd['id'], order=None, verbose=True)
            elif vehicle != 'auto':
                cat = modelwiki.get_category_object_in_location(
                    model_wd['id'], street_wd['id'], order=digital_number, verbose=True)
            if cat is not None:
                model_in_location_found = True
                categories.add(cat)
                
            else:
                if model_wd["commons"] is None:
                    raise ValueError('vehicle model https://www.wikidata.org/wiki/' +
                             model_wdid+' must has commons category')
                if vehicle != 'auto':
                    categories.discard(model_wd["commons"]) #remove from set if exist
                    categories.add(model_wd["commons"] +
                                   '|' + digital_number)
                elif vehicle == 'auto':
                    categories.discard(model_wd["commons"]) #remove from set if exist
                    categories.add(model_wd["commons"])
        
        # SUBCLASS OF AUTOMOBILE IN LOCATION
        if vehicle == 'auto':
            subclasses = model_wd['claims'].get('P279',None)
            if subclasses is None:
                self.logger.info('🤏 subclass of car model in wikidata is null, skipped')
            else:
                for subclass in subclasses:
                    cat = modelwiki.get_category_object_in_location(
                    subclass['value'], street_wd['id'], order=None, verbose=True)
                    categories.add(cat)
                    break
        
        
        # TRANSPORT IN CITY
        if 'system_wd' in locals():
            if vehicle not in train_synonims and model_in_location_found == False and has_category_for_this_vehicle == False :
                categories.add(system_wd['commons'])
                
        # categories for secondary_wikidata_ids
        # search for geography categories using street like (ZIU-9 in Russia)

        if type(secondary_wikidata_ids) == list and len(secondary_wikidata_ids) > 0:
            for wdid in secondary_wikidata_ids:
                cat = modelwiki.get_category_object_in_location(
                    wdid, street_wdid, verbose=True)
                if cat is not None:
                    categories.add(cat)
                else:
                    wd_record = modelwiki.get_wikidata_simplified(wdid)
                    if wd_record is None:
                        return None
                    secondary_objects_should_have_commonscat = False
                    if secondary_objects_should_have_commonscat:
                        assert 'commons' in wd_record, 'https://www.wikidata.org/wiki/' + \
                            wdid + ' must have commons'
                        assert wd_record["commons"] is not None, 'https://www.wikidata.org/wiki/' + \
                            wdid + ' must have commons'

                    if 'commons' in wd_record and wd_record["commons"] is not None:
                       categories.add(wd_record['commons'])
        categories.discard(None)
        for catname in categories:
            
            assert catname is not None, 'none value in categories:' + str(categories)+' '+filename
            catname = catname.replace('Category:', '')
            text += "[[Category:"+catname+"]]" + "\n"
        
        #optional add city to SDC by coordinate

        city_wdid = None
        if os.path.isfile('building-generator.gpkg'):
            city_wdid = self.get_place_from_input(filename,'building-generator.gpkg',geo_dict,layer='cities',override_key='_city',geodata_attribute='wikidata') or ''
            if city_wdid is not None: wikidata_4_structured_data.add(city_wdid)
            
        # add transport type to SDC
        # vehicle to wikidata
        vehicles_wikidata = {"trolleybus": "Q5639", "bus": "Q5638",
                             "tram": "Q3407658", "auto": "Q1420", "locomotive": "Q93301", "train": "Q870"}
        if vehicle in vehicles_wikidata:
            wikidata_4_structured_data.add(vehicles_wikidata[vehicle])
        if vehicle in train_synonims:
            wikidata_4_structured_data.add(vehicles_wikidata['train'])

        assert None not in wikidata_4_structured_data, 'empty value added to structured data set:' + \
            str(' '.join(list(wikidata_4_structured_data)))
        return {"name": commons_filename, 
        "text": text,
                "structured_data_on_commons": list(wikidata_4_structured_data),
                "country":country,
                'captions': captions,
                'need_create_categories':need_create_categories,
                'location_of_creation':street_wdid,
                "dt_obj": dt_obj}
                
    def get_suffix_from_string(self,test_str:str)->str:
        if not('suffix' in test_str.lower()):
            return ''
            
        import re
        # cut to . symbol if extsts
        test_str = test_str[0:test_str.index('.')]

        lst = re.findall(r'(suffix\d+)', test_str)
        suffix=lst[0].replace('suffix','')
        return suffix

    def get_colorlist_from_string(self, test_str: str) -> list:
        # from string 2002_20031123__r32_colorgray_colorblue.jpg  returns [Gray,Blue]
        # 2002_20031123__r32_colorgray_colorblue.jpg

        import re
        # cut to . symbol if extsts
        test_str = test_str[0:test_str.index('.')]

        # split string by _
        parts = re.split('_+', test_str)

        lst = list()
        for part in parts:
            if part.startswith('color'):
                lst.append(part[5:].title())

        return lst
        
    def get_facing_from_string(self, test_str: str) -> str:
        # from string 2002_20031123__r32_facingThree-quarter.jpg  returns 'Three-quarter]
        # 2002_20031123__r32_colorgray_colorblue.jpg

        import re
        # cut to . symbol if extsts
        test_str = test_str[0:test_str.index('.')]

        # split string by _
        parts = re.split('_+', test_str)

        lst = list()
        for part in parts:
            if part.startswith('facing'):
                #lst.append(part[5:].title())
                text = part[len('facing'):].upper()
                return text

        return lst
        
    def get_licenceplate_from_string(self, test_str: str) -> str:
        # from string 2002_20031123_lpA 123 BC 99_.jpg  returns [A 123 BC 99]
        
        if '_np' not in test_str: 
            return ''

        import re
        # cut to . symbol if extsts
        test_str = test_str[0:test_str.index('.')]

        # split string by _
        parts = re.split('_+', test_str)

        lst = list()

        for part in parts:
            if part.startswith('np'):
                lst.append(part[2:].upper())
             
        return lst[0]
    
    def get_replace_id_from_string(self, test_str: str) -> str:
        '''
        from string 12345_replace56911685.jpg returns M56911685
        '''
        import re
        # cut to . symbol if extsts
        test_str = test_str[0:test_str.index('.')]

        lst = re.findall(r'(replace\d+)', test_str)
        id=lst[0].replace('replace','')
        return id
    
    def get_wikidatalist_from_string(self, test_str: str) -> list:
        ''' from string 
        2002_20031123__r32_colorgray_colorblue_Q111_Q12345_wikidataAntonovka_placeUUID12345.jpg  
        returns [Q111,Q12345,UUID12345]



print python code for extract substrings from string as list
given string 2002_20031123__r32_colorgray_colorblue_Q111_Q12345_wikidataAntonovka_placeUUIDGvVFYJM
substrings is start with Q or UUID and end with '_' or end of string
must return ['Q111','Q12345','UUIDGvVFYJM']

        '''
        import re
        test_str = os.path.basename(test_str)
        # cut to . symbol if extsts
        test_str = test_str[0:test_str.index('.')]
        lst = re.findall(r'(Q[^\W_]*|UUID[^\W_]*)(?=_|$)', test_str)
        if 'UUID' in test_str:
            uuids2wikidata = self.load_local_wikidata_uuids()
            lst = [uuids2wikidata[item] if 'uuid' in item.lower() else item for item in lst]
        lst = [item for item in lst if len(item) > 1] #remove element 1 char lenght

        return lst
    
    

    
    
    def get_categorieslist_from_string(self, test_str: str) -> list:
        '''
        from string 2002_20031123__r32_colorgray_colorblue_Q12345_wikidataAntonovka_catid34567.jpg  reads [34567], and returns category names for this ids
        '''
        def get_categoriesid_from_string(test_str: str) -> list:
            ''' from string 2002_20031123__r32_colorgray_colorblue_Q12345_wikidataAntonovka_catid34567.jpg  returns [34567]
            # 2002_20031123__r32_colorgray_colorblue.jpg
            '''
            import re
            # cut to . symbol if extsts
            test_str = test_str[0:test_str.index('.')]
            lst = re.findall(r'(catid\d+)', test_str)
            return lst
        
        from model_wiki import Model_wiki as Model_wiki_ask
        modelwiki = Model_wiki_ask()
        
        category_ids = get_categoriesid_from_string(test_str)
        if not len(category_ids)>0:
            return list()
        else:
            categories=list()
            for category_id in category_ids:
                category=modelwiki.pagename_from_id(category_id.replace('catid',''))
                if category is not None:
                    categories.append(category)
            return categories
       
    def load_local_wikidata_uuids(self)->dict:
        import jsonlines
        # read from local cache
        with jsonlines.open('local_wikidata_uuids.json') as reader:
            list_of_dicts = [obj for obj in reader]
            uuid2wdid = {d['uuid']: d['wdid'] for d in list_of_dicts}
            return uuid2wdid

    def get_placewikidatalist_from_string(self, test_str: str) -> list:
        # from string 2002_20031123__r32_colorgray_colorblue_locationQ12345_wikidataAntonovka.jpg  returns [Q12345]
        # 2002_20031123__r32_colorgray_colorblue.jpg

        import re
        # cut to . symbol if extsts
        startpos=test_str.index('place')
        endpos=test_str[startpos:].index('.')+startpos
        test_str = test_str[startpos:endpos]

        if 'placeUUID' in test_str:

            lst = re.findall(r'(placeUUID\d+)', test_str)

            lst2 = list()
            for line in lst:
                lst2.append(line[8:])
            lst = lst2
            del lst2
            
            local_wikidata_uuid=lst
            # read from local cache
            uuid2wdid = self.load_local_wikidata_uuids()
            return uuid2wdid[local_wikidata_uuid]


        
        lst = re.findall(r'(placeQ\d+)', test_str)

        lst2 = list()
        for line in lst:
            lst2.append(line[5:])
        lst = lst2
        del lst2
        if 'placeQ' in test_str:
            assert len(lst)>0
            assert lst[0].startswith('Q'), lst[0] + \
                ' get instead of wikidata id'

        return lst
        
    def get_mapillary_from_string(self, test_str: str) -> list:
        # from string aaaa_mapillarykey123456_mapillaryuservasya.jpg  returns [123456,vasya]
        # 2002_20031123__r32_colorgray_colorblue.jpg
        
        if 'mapillarykey' not in test_str and 'mapillaryuser' not in test_str: return None,None

        import re
        # cut to . symbol if extsts
        test_str = test_str[0:test_str.index('.')]

        lst = re.findall(r'(mapillarykey\d+)', test_str)

        lst2 = list()
        for line in lst:
            lst2.append(line[12:])
        mapillarykey=str(lst2)
        
        test_str = test_str[0:test_str.index('.')]
        lst = re.findall(r'(mapillaryuser\d+)', test_str)

        lst2 = list()
        for line in lst:
            lst2.append(line[13:])
        mapillaryuser=str(lst2)

        return mapillarykey,mapillaryuser


        
    def get_date_information_part(self, dt_obj, taken_on_location):
        st = ''
        st += (
            """|date="""
            + "{{Taken on|"
            + dt_obj.isoformat()
            + "|location="
            + taken_on_location
            + "|source=EXIF}}"
            + "\n"
            
        )
        return st 
        
    def get_source_information_part(self, filename):
        mapillarykey,mapillaryuser=self.get_mapillary_from_string(filename)
        if mapillarykey is None and mapillaryuser is None:
            text = "\n" +"|source={{own}}\n|author={{Creator:" + self.photographer+"}}"
        else:
            #text = f"\n"
            text = "\n" +"""|source= {{Mapillary-source|key="""+mapillarykey+"""}}|author= [http://www.mapillary.com/profile/"""+mapillaryuser+' '+mapillaryuser+'] @ Mapillary.com'
        
        return text

    def get_tech_description(self, filename, geo_dict):
        mapillarykey,mapillaryuser=self.get_mapillary_from_string(filename)
        text = ''
        #if 'stitch' in filename or 'pano' in filename.lower():
        if any(substring in filename.lower() for substring in ('stitch','pano','photosphere')):
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
        camera_text, camera_categories = self.get_camera_text(filename)
        text += camera_text

        if mapillarykey is None and mapillaryuser is None:
            text = (text + '== {{int:license-header}} =='+"\n"+placejpgconfig.license+"\n\n" )
        else:
            text = (text + '== {{int:license-header}} =='+"\n"+'{{cc-by-sa-4.0|'+mapillaryuser+'}}'+"\n\n" )
        categories = set()
        categories.update(camera_categories)


        if 'ShiftN' in filename:
            categories.add('Corrected with ShiftN')
        if 'stitch' in filename or 'pano' in filename.lower():
            categories.add('Photographs by ' + self.photographer + '/Stitched panoramics')
        categories.add('Uploaded with Placejpg')

        return text,categories


    def read_IPTC(self,filepath)->dict:
    
        # read IPTC
        info = IPTCInfo(filepath, force=True)
        city = None
        sublocation = None
        objectname = None

        if info['city'] is not None:
            city = info['city'].decode('UTF-8')
        if info['sub-location'] is not None:
            sublocation = info['sub-location'].decode('UTF-8')
        if info['object name'] is not None:
            try:
                objectname = info['object name'].decode('UTF-8')
            except:
                objectname = info['object name'].decode('CP1251')
        caption = info['caption/abstract']
        if caption is not None:
            try:
                caption = caption.decode('UTF-8')
            except:
                caption = caption.decode('CP1251')
        else:
            caption = ''
        
        if objectname is None or caption is None: return None
        result = dict()
        result['object name']=objectname
        result['caption']=caption
        return result

    def make_image_texts_simple(
        self, filename, wikidata, country='', rail='', secondary_wikidata_ids=list(), custom_categories=list(), suffix=''
    ) -> dict:
        # return file description texts
        # there is no excact 'city' in wikidata, use manual input cityname

        from model_wiki import Model_wiki as Model_wiki_ask
        modelwiki = Model_wiki_ask()

        need_create_categories = list()
        wikidata_4_structured_data = set()
        location_of_creation = ''
        


        assert os.path.isfile(filename), 'not found '+filename

        categories = set()
        # obtain exif

        dt_obj = self.image2datetime(filename)
        iptc_objectname = self.image2objectname(filename)
        geo_dict = self.image2coords(filename)
        

        # Optionaly obtain wikidata from gpkg file if wikidata parameter is path to vector file (.gpkg)
        if os.path.isfile(wikidata):
            street=wikidata
            wikidata = self.get_place_from_input(filename,street,geo_dict)
            location_of_creation = wikidata
            del street
            if wikidata is None:
                #place should taken from gpkg, but not found
                return None

        # Optionaly obtain country from gpkg file if country parameter is path to vector file (.gpkg)
        if os.path.isfile(country):
            country = self.get_place_from_input(filename,country,geo_dict,override_key='_location',geodata_attribute='name:en')
            if country is None:
                #place should taken from gpkg, but not found
                return None   
        
        # Optionaly obtain prefix from gpkg file
        prefix = ''
        if os.path.isfile('prefixes.gpkg'):
            prefix = self.get_place_from_input(filename,'prefixes.gpkg',geo_dict,override_key='_prefix',geodata_attribute='name:en') or ''
                
        wd_record = modelwiki.get_wikidata_simplified(wikidata)
        
        if wd_record["commons"] is None: 
            self.logger.error('https://www.wikidata.org/wiki/' + \
            wikidata + ' must have commons')
            return None

        instance_of_data = list()
        if 'P31' in wd_record['claims']:
            for i in wd_record['claims']['P31']:
                instance_of_data.append(
                    modelwiki.get_wikidata_simplified(i['value']))
        
        iptc_captions = self.read_IPTC(filename)

        
        text = ""
        objectnames = {}
        objectname_long = {}
        objectnames_long = {}

        #rewrite label if not extst
        for lang in self.langs_primary:
            if lang not in wd_record['labels']:
                
                self.logger.error('object https://www.wikidata.org/wiki/' +
                    wd_record['id']+' must has name '+lang)
                return None
                wd_record['labels'][lang]=wd_record['labels']['en']
                #self.logger.error('object https://www.wikidata.org/wiki/' +
                #                 wd_record['id']+' must has name '+lang)
                #return None
            objectnames[lang] = wd_record['labels'][lang]
            objectname_long[lang] = objectnames[lang]

        for lang in self.langs_optional:
            if lang in wd_record['labels']:
                objectnames[lang] = wd_record['labels'][lang]


        # BUILD DESCRIPTION FROM 'INSTANCE OF' NAMES
        #  
        if len(instance_of_data) > 0:
            for lang in self.langs_primary:
                for i in instance_of_data:
                    if lang not in i['labels']:
                        self.logger.error('object https://www.wikidata.org/wiki/' +
                                 i['id']+' must has name '+lang)
                        return None
                objectname_long[lang] = ', '.join(
                d['labels'][lang] for d in instance_of_data if d['labels'][lang].upper() not in objectnames[lang].upper()) + ' '+objectnames[lang]

            for lang in self.langs_optional:
                try:
                    objectnames_long[lang] = ', '.join(
                        d['labels'][lang] for d in instance_of_data if d['labels'][lang].upper() not in objectnames[lang].upper()) + ' '+objectnames[lang]
                except:
                    pass
        else:
            for lang in self.langs_primary:
                if lang in objectnames:  objectname_long[lang] = objectnames[lang]
            for lang in self.langs_optional:
                if lang in objectnames:   objectname_long[lang] = objectnames[lang]

        """== {{int:filedesc}} ==
{{Information
|description={{en|1=2nd Baumanskaya Street 1 k1}}{{ru|1=Вторая Бауманская улица дом 1 К1}} {{on Wikidata|Q86663303}}  {{Building address|Country=RU|Street name=2-я Бауманская улица|House number=1 К1}}  
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

        if iptc_captions is not None and iptc_captions['objectname']!='':
            st += iptc_captions['objectname']
            
        if iptc_captions is not None and iptc_captions['caption']!='':
            st += iptc_captions['caption']
            

        for lang in self.langs_primary:
            st += "{{"+lang+"|1=" + objectname_long[lang] + "}} \n"

        for lang in self.langs_optional:
            if lang in objectnames_long:
                st += "{{"+lang+"|1=" + objectnames_long[lang] + "}} \n"

        st += " {{on Wikidata|" + wikidata + "}}\n"
        if len(secondary_wikidata_ids) > 0:
            for secondary_wikidata_id in secondary_wikidata_ids:
                if secondary_wikidata_id == wikidata: continue
                st += " {{on Wikidata|" + secondary_wikidata_id + "}}\n"
        
        # CULTURAL HERITAGE
        # if main object is cultural heritage: insert special templates
        heritage_id = None
        heritage_id = modelwiki.get_heritage_id(wikidata)
        if heritage_id is not None:
            st += "{{Cultural Heritage Russia|" + heritage_id + "}}"
            today = datetime.today()
            if today.strftime('%Y-%m') == '2024-09':
                st += "{{Wiki Loves Monuments 2024|ru}}"
                
        # wikidata depicts
        st += """ |other_fields_1 = 
{{Information field
 |name  = {{Label|P180|link=-|capitalization=ucfirst}} 
 |value = {{#property:P180|from=M{{PAGEID}} }} }} \n"""

        st += self.get_date_information_part(dt_obj, country)
        st += self.get_source_information_part(filename)
        st += "}}\n"

        text += st

        tech_description, tech_categories = self.get_tech_description(filename, geo_dict)
        text = text + tech_description

        del tech_description
        categories.update(tech_categories)

        # USERCAT BY THEME
        usercat_categories = set()
        
        # PHOTOS OF USER IN COUNTRY
        CategoryUserInCountry = ''
        CategoryUser = 'Photographs by '+self.photographer
        cat = 'Photographs by {photographer}/{country}'
        cat = cat.format(photographer=self.photographer,
                         country=country,
                        )           
        cat_content='''{{Usercat}}
{{GeoGroup}}
[[Category:'''+CategoryUser+''']]
[[Category:Photographs of '''+country+''' by photographer]]'''
        need_create_categories.append({'name':cat,'content':cat_content})
        CategoryUserInCountry = cat
        
        # PHOTOS OF USER IN COUNTRY WITH ARCHITECTURE STYLE
        
        #check is any wikidata object is building and it has architecture style with commons category
        prop='P149' #architecture style
        temp_wikidata_list = list()
        temp_wikidata_list = secondary_wikidata_ids+[wikidata]
        for wdid in temp_wikidata_list:
            wd=modelwiki.get_wikidata_simplified(wdid)
            if prop in wd['claims']:
                for claim in wd['claims'][prop]:
                    cat_for_claim=''
                    cat_for_claim = modelwiki.get_wikidata_simplified(claim['value'])['commons']    
                    cat_for_claim = f'{CategoryUserInCountry}/{cat_for_claim}'
                    cat_content='''{{Usercat}}
{{GeoGroup}}
[[Category:'''+CategoryUserInCountry+''']]'''
                    need_create_categories.append({'name':cat_for_claim,'content':cat_content})
                    usercat_categories.add(cat_for_claim)
                    del cat_for_claim
        
        # SUBCLASS OF ARCHITECTURAL ELEMENT
        temp_wikidata_list = list()
        temp_wikidata_list = secondary_wikidata_ids+[wikidata]
        for wdid in temp_wikidata_list:
            if modelwiki.is_subclass_of(wdid,'Q391414'):
                wd=modelwiki.get_wikidata_simplified(wdid)    
                cat_for_claim=''
                cat_for_claim = f'{CategoryUserInCountry}/Architectural elements'
                cat_content='''{{Usercat}}
{{GeoGroup}}
[[Category:'''+CategoryUser+'''/Architectural elements]]
[[Category:'''+CategoryUserInCountry+''']]'''
                need_create_categories.append({'name':cat_for_claim,'content':cat_content})
                usercat_categories.add(cat_for_claim)
                
                cat_for_claim = f'{CategoryUser}/Architectural elements'
                cat_content='''{{Usercat}}
{{GeoGroup}}
[[Category:'''+CategoryUser+''']]
'''
                need_create_categories.append({'name':cat_for_claim,'content':cat_content})                  
                del cat_for_claim
                
        # BUILING DATE START
        temp_wikidata_list = list()
        temp_wikidata_list = secondary_wikidata_ids+[wikidata]
        for wdid in temp_wikidata_list:
            # is this building but not transport infrastructure (station)
            if modelwiki.is_subclass_of_building(wdid) and not modelwiki.is_subclass_of(wdid,'Q376799'):
                wd=modelwiki.get_wikidata_simplified(wdid)
                prop=''
                if 'P1619' in wd['claims']: 
                    prop='P1619' #date of official opening
                elif  'P571' in wd['claims']:
                    prop='P571' #date of official opening
                else:
                    continue
                for claim in wd['claims'][prop]:
                    decade=claim['value'][:3]+'0'
                    cat_for_claim = f'{CategoryUserInCountry}/{decade}s architecture'
                    cat_content='''{{Usercat}}
{{GeoGroup}}
[[Category:'''+CategoryUserInCountry+''']]
[[Category:'''+CategoryUser+'/'+decade+'''s architecture]]
'''
                    need_create_categories.append({'name':cat_for_claim,'content':cat_content})
                    usercat_categories.add(cat_for_claim)
                    
                    cat_for_claim = f'{CategoryUser}/{decade}s architecture'
                    cat_content='''{{Usercat}}
{{GeoGroup}}
[[Category:'''+CategoryUser+''']]
'''
                    need_create_categories.append({'name':cat_for_claim,'content':cat_content})                  
                    del cat_for_claim
                        
        
        # END OF USERCAT CHECKS
        # when not found any special user categories: use CategoryUserInCountry       
        if len(usercat_categories)==0:
            usercat_categories.add(CategoryUserInCountry)
        
        categories.update(usercat_categories)
        categories.update(custom_categories)
        # END USERCAT BY THEME
        
        if rail:
            text += "[[Category:Railway photographs taken on " + \
                dt_obj.strftime("%Y-%m-%d")+"]]" + "\n"
            if isinstance(country, str) and len(country) > 3:
                text += "[[Category:" + \
                    dt_obj.strftime("%B %Y") + \
                    " in rail transport in "+country+"]]" + "\n"

            
        if len(secondary_wikidata_ids) < 1:
            text = text + "[[Category:" + wd_record["commons"] + "]]" + "\n"
        else:
            text = text + "[[Category:" + wd_record["commons"] + "]]" + "\n"
            for wdid in secondary_wikidata_ids:
                cat = modelwiki.get_category_object_in_location(
                    wdid, wikidata, verbose=True)
                if cat is not None:
                    categories.add(cat)
                else:
                    wd_record = modelwiki.get_wikidata_simplified(wdid)
                    if wd_record.get('commons',None) is not None:
                        categories.add(wd_record["commons"])

                    
        for catname in categories:
            catname = catname.replace('Category:', '')
            text += "[[Category:"+catname+"]]" + "\n"
        
        # COPY INSTANCE_OF FROM MAIN OBJECT TO STRUCTURED DATA
        if len(instance_of_data) > 0:
            for element in instance_of_data:  
                wikidata_4_structured_data.add(element['id'])
        
        
        if suffix == '':
            skip_unixtime=False
        else:
            skip_unixtime=True
        commons_filename = self.commons_filename(
            filename, objectnames, wikidata, dt_obj, add_administrative_name=False, prefix=prefix, suffix=suffix, skip_unixtime=skip_unixtime)

        return {"name": commons_filename, 
                "text": text, 
                "dt_obj": dt_obj,
                "country":country,
                "structured_data_on_commons": list(wikidata_4_structured_data),
                "location_of_creation":location_of_creation,
                "need_create_categories":need_create_categories,
                "wikidata":wikidata}

    def commons_filename(self, filename, objectnames, wikidata, dt_obj, add_administrative_name=True, prefix='', suffix='', skip_unixtime=False) -> str:
        # file name on commons

        from model_wiki import Model_wiki as Model_wiki_ask
        modelwiki = Model_wiki_ask()

        filename_base = os.path.splitext(os.path.basename(filename))[0]
        filename_extension = os.path.splitext(os.path.basename(filename))[1]
        # if this is building: try get machine-reading address from https://www.wikidata.org/wiki/Property:P669
        building_info = modelwiki.get_building_record_wikidata(
            wikidata, stop_on_error=False)
        if building_info is not None:

            objectnames['en'] = (
                building_info["addr:street:en"]
                + " "
                + building_info["addr:housenumber:en"]
            )

        commons_filename = ''
        
        if prefix != '':
            if prefix not in objectnames['en']:
                commons_filename = f"{prefix}_"

        if suffix != '':  suffix =   '_'+suffix
        
        if skip_unixtime:
            time_suffix_format="%Y-%m"
        else:
            time_suffix_format="%Y-%m %s"
        
        
        commons_filename = (
            commons_filename + objectnames['en'] + " " +
            dt_obj.strftime(time_suffix_format) + suffix + filename_extension
        )
        commons_filename = commons_filename.replace("/", " drob ")


        # add district name to file name
        if add_administrative_name:
            try:
                administrative_name = modelwiki.get_wikidata_simplified(modelwiki.get_upper_location_wdid(
                    modelwiki.get_wikidata_simplified(wikidata)))['labels']['en']
                commons_filename = administrative_name + '_'+commons_filename
            except:
                pass

        return commons_filename

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

        from model_wiki import Model_wiki
        modelwiki = Model_wiki()

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
            obj_wdid = modelwiki.wikidata_input2id(obj_wdid)
            obj_wd = modelwiki.get_wikidata_simplified(obj_wdid)
            objects_wikidata.append(obj_wd)

        if self.is_wikidata_id(city):
            city_wdid = city
        else:
            city_wdid = self.search_wikidata_by_string(
                city, stop_on_error=True)
        city_wd = modelwiki.get_wikidata_simplified(city_wdid)

        # get country, only actual values.
        
        country_wdid = modelwiki.get_best_claim(city_wdid,'P17')
        country_wd = modelwiki.get_wikidata_simplified(country_wdid)

        try:
            dt_obj = self.image2datetime(filename)
        except:
            assert date is not None, 'in image '+filename + \
                'date can not be read from exif, need set date in --date yyyy-mm-dd'
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
            if 'aliaces' in obj_wd:
                aliases = obj_wd['aliases'].get('en', None)
                if type(aliases) == list and len(aliases) > 0:
                    keywords += aliases

        keywords.append(city_wd['labels']['en'])
        keywords.append(city_wd['labels']['ru'])
        keywords.append(country_wd["labels"]["ru"])

        return d, keywords

    def get_camera_text(self, filename) -> list:
        st = ''
        categories = set()
        image_exif = self.image2camera_params(filename)
        lens_invalid_names=('0.0 mm f/0.0',)
        cameramodels_dict = {
                    'Pentax corporation PENTAX K10D': 'Pentax K10D',
                    'Pentax PENTAX K-r': 'Pentax K-r',
                    'Samsung techwin co. SAMSUNG GX10': 'Samsung GX10',
                    'Gopro HERO8 Black': 'GoPro Hero8 Black',
                    'Samsung SM-G7810': 'Samsung Galaxy S20 FE 5G',
                    'Olympus imaging corp.': 'Olympus',
                    'Nikon corporation NIKON': 'Nikon',
                    'Panasonic': 'Panasonic Lumix',
                    'Hmd global Nokia 5.3': 'Nokia 5.3',
                    'COOLPIX':'Coolpix',
                    'Fujifilm FinePix REAL 3D W3':'Fujifilm FinePix Real 3D W3',
                    'Ricoh RICOH THETA S':'Ricoh Theta S'
                }
        lensmodel_dict = {
                    'OLYMPUS M.12-40mm F2.8': 'Olympus M.Zuiko Digital ED 12-40mm f/2.8 PRO',
                    'smc PENTAX-DA 35mm F2.4 AL': 'SMC Pentax-DA 35mm F2.4',
                    'smc PENTAX-DA 14mm F2.8 EDIF': 'SMC Pentax DA 14 mm f/2.8 ED IF',
                }
        lens = None
        if image_exif.get("make") is not None and image_exif.get("model") is not None:
            if image_exif.get("make") != "" and image_exif.get("model") != "":
                make = image_exif.get("make").strip()
                model = image_exif.get("model").strip()
                make = make.capitalize()
                st = "{{Taken with|" + make + " " + model + "|sf=1|own=1}}" + "\n"

                st += '{{Photo Information|Model = ' + make + " " + model
                if image_exif.get("lensmodel", '') != "" and image_exif.get("lensmodel", '') != "":
                    lens = image_exif.get("lensmodel")
                    if lens in lens_invalid_names:
                        lens = None
                if lens is not None:
                    st += '|Lens = ' + image_exif.get("lensmodel")
                    
                def aperture2wikicommons(val:float)->str:
                    val = round(float(val),1)
                    if val.is_integer():
                        return str(int(val))
                    return str(val)
                    

                if image_exif.get("fnumber", '') != "" and image_exif.get("fnumber", '') != "" and int(image_exif.get("fnumber", 0)) != 0:
                    aperture_text=aperture2wikicommons(image_exif.get("fnumber"))
                    st += '|Aperture = f/' + aperture_text
                    categories.add('F-number f/'+aperture_text)
                if image_exif.get("'focallengthin35mmformat'", '') != "" and image_exif.get("'focallengthin35mmformat'", '') != "":
                    st += '|Focal length 35mm = f/' + \
                        str(image_exif.get("'focallengthin35mmformat'"))
                st += '}}' + "\n"


                if image_exif.get('usepanoramaviewer')==True: st += "{{Pano360}}"+ "\n"
                if image_exif.get("focallength", '') != "" and image_exif.get("focallength", '') != "" and int(image_exif.get("focallength", 0)) != 0:
                    categories.add(
                        'Lens focal length '+str(round(float(image_exif.get("focallength",0))))+' mm')

                if image_exif.get("iso", '') != "" and image_exif.get("iso", '') != "": 
                    try:
                        if int(image_exif.get("iso",0))>49:
                            try:
                                categories.add(
                                'ISO speed rating '+str(round(float(str(image_exif.get("iso")))))+'')
                            except:
                                self.logger.info('ISO value is bad:'+str(image_exif.get("iso", '')))
                    except:
                        pass

                for camerastring in cameramodels_dict.keys():
                    if camerastring in st:
                        st = st.replace(
                            camerastring, cameramodels_dict[camerastring])

                # lens quess
                if lens is not None:
                    st += "{{Taken with|" + lens.replace(
                        '[', '').replace(']', '').replace('f/ ', 'f/') + "|sf=1|own=1}}" + "\n"

                for lensstring in lensmodel_dict.keys():
                    if lensstring in st:
                        st = st.replace(lensstring, lensmodel_dict[lensstring])

                st = st.replace('Canon Canon', 'Canon')

                return st, categories
        else:
            return '', categories

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
        if path.lower().endswith('.stl'):
            return True

        cmd = [self.exiftool_path, path, "-datetimeoriginal", "-csv"]
        process = subprocess.run(cmd, stdout=subprocess.DEVNULL)

        if process.returncode == 0:
            return True
        else:
            return False

    def check_extension_valid(self, filepath) -> bool:
        ext = os.path.splitext(filepath)[1].lower()[1:]
        allowed = ['tiff', 'tif', 'png', 'gif', 'jpg', 'jpeg', 'webp', 'xcf', 'mid', 'ogg', 'ogv',
                   'svg', 'djvu', 'stl', 'oga', 'flac', 'opus', 'wav', 'webm','mp4','mov', 'mp3', 'midi', 'mpg', 'mpeg','avi']
        if ext in allowed:
            return True
        return False

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
                    if path.lower().endswith(('.mp4','.mov','.avi')):
                        cmd = [self.exiftool_path, path, "-createdate", "-csv"]
                        self.logger.debug('video')

                    exiftool_text_result = subprocess.check_output(cmd)
                    tmp = exiftool_text_result.splitlines()[1].split(b",")
                    if len(tmp) > 1:
                        dt_str = tmp[1]
                        if ':' in str(dt_str):
                            dt_obj = datetime.strptime(
                                dt_str.decode("UTF-8"), "%Y:%m:%d %H:%M:%S"
                            )
            elif path.lower().endswith('.stl'):
                dt_obj = None

            if dt_obj is None:
                dt_obj = get_datetime_from_string(os.path.basename(path))
                

            if dt_obj is None:
                return None
            return dt_obj
            
            
    def image2objectname(self,path)->str:

        return ''
    
    def image2coords(self, path):
        exiftool_metadata = self.image2camera_params(path)
        try:
            
            lat = round(float(exiftool_metadata.get('gpslatitude')), 6)
            lon = round(float(exiftool_metadata.get('gpslongitude')), 6)
        except:
            pass
            lat,lon = self.get_coordinate_from_string(path)
        
        if lat is None and lon is None:
            self.logger.warning('no coordinates in '+path)
            return None

        geo_dict = {}
        geo_dict = {"lat": lat, "lon": lon}
        if 'gpsimgdirection' in exiftool_metadata:
            geo_dict["direction"] = round(
                float(exiftool_metadata.get('gpsimgdirection')))

        if 'gpsdestlatitude' in exiftool_metadata:
            geo_dict["dest_lat"] = round(
                float(exiftool_metadata.get('gpsdestlatitude')), 6)
        if 'gpsdestlongitude' in exiftool_metadata:
            geo_dict["dest_lon"] = round(
                float(exiftool_metadata.get('gpsdestlongitude')), 6)

        return geo_dict

    def prepare_commonsfilename(self, commonsfilename)->str:
        commonsfilename = commonsfilename.strip()
        if commonsfilename.startswith("File:") == False:
            commonsfilename = "File:" + commonsfilename
        commonsfilename = commonsfilename.replace("_", " ")
        return commonsfilename

   
    def print_structured_data(self, commonsfilename):
        warnings.warn('moved to model_wiki', DeprecationWarning, stacklevel=2)
        commonsfilename = self.prepare_commonsfilename(commonsfilename)
        commons_site = pywikibot.Site("commons", "commons")

        # File to test and work with

        page = pywikibot.FilePage(commons_site, commonsfilename)

        # Retrieve Wikibase data
        item = page.data_item()
        item.get()

        for prop in item.claims:
            for statement in item.claims[prop]:
                if isinstance(statement.target, pywikibot.page._wikibase.ItemPage):
                    print(prop, statement.target.id,
                          statement.target.labels.get("en"))
                else:
                    print(prop, statement.target)

    


    
    

    def process_and_upload_files(self, filepath, desc_dict):
        from model_wiki import Model_wiki
        modelwiki = Model_wiki()
        if not os.path.exists(filepath):
            print(filepath.ljust(50)+' '+' not exist')
            quit()
        assert os.path.exists(filepath)
        #asap quicker check if directory is empty
        if os.listdir(filepath) == []: quit()
        assert desc_dict['mode'] in ['object', 'vehicle', 'auto', 'bus']

        assert 'country' in desc_dict

        if not 'secondary_objects' in desc_dict:
            # for simple call next function
            desc_dict['secondary_objects'] = list()
        if not 'dry_run' in desc_dict:
            desc_dict['dry_run'] = False  # for simple call next function
        if not 'later' in desc_dict:
            desc_dict['later'] = False  # for simple call next function
        if not 'verify' in desc_dict:
            desc_dict['verify'] = False  # for simple call next function
        if 'country' in desc_dict:
            desc_dict['country'] = desc_dict['country'].title()
        else:
            desc_dict['country'] = None

        files, uploaded_folder_path = self.input2filelist(filepath)

        if len(files) == 0:
            quit()

        dry_run = desc_dict['dry_run']
        if desc_dict['later'] == True:
            dry_run = True

        uploaded_paths = list()
        files_filtered = list()
        # count for progressbar
        total_files = 0
        pbar = tqdm(files)
        for filename in pbar:
            pbar.set_description(filename)
            if 'commons_uploaded' in filename:
                continue
            if self.check_extension_valid(filename):
                if self.check_exif_valid(filename) :
                    files_filtered.append(filename)
                    total_files = total_files + 1
                else:
                    self.logger.info(filename+' invalid')
    
        progressbar_on = False
        if total_files > 1 and 'progress' in desc_dict:
            progressbar_on = True
            pbar = tqdm(total=total_files)
        
        files = files_filtered
        del files_filtered
        
        for filename in files:
            if 'commons_uploaded' in filename:
                continue
            assert '_place'+' ' not in filename
            
            if not(os.path.isfile(filename)):
                # this section goes when upload mp4: mp4 converted to webp, upload failed, then run second time, mp4 moved, webp uploaded, ciycle continued   
                continue
            
            
            secondary_wikidata_ids = modelwiki.input2list_wikidata(
                desc_dict['secondary_objects'])

            # get wikidata from filepath

            if secondary_wikidata_ids == [] and ('_Q' in filename or 'placeQ' in filename or 'UUID' in filename):
                secondary_wikidata_ids = self.get_wikidatalist_from_string(
                    filename)
            
            # get custom categories without wikidata from filename
            # i use it for film rolls
            
            #display image in terminal
            subprocess.run(['climage','--unicode','--truecolor',filename])
            
            custom_categories = list()
            custom_categories = self.get_categorieslist_from_string(filename)
            
            suffix=self.get_suffix_from_string(filename)
            
            if desc_dict['mode'] == 'object':
                if desc_dict['wikidata'] == 'FROMFILENAME':
                    if not self.get_wikidatalist_from_string(filename):
                        self.logger.error(filename.ljust(
                            80)+': no wikidata in filename, skip upload')
                        continue  # continue to next file
                    wikidata = self.get_wikidatalist_from_string(filename)[0]
                    del secondary_wikidata_ids[0]
                else:
                    if os.path.isfile(desc_dict['wikidata']):
                        wikidata=desc_dict['wikidata']
                    else:
                        wikidata = modelwiki.wikidata_input2id(
                        desc_dict['wikidata'])

                texts = self.make_image_texts_simple(
                    filename=filename,
                    wikidata=wikidata,
                    country=desc_dict['country'],
                    rail=desc_dict.get('rail'),
                    secondary_wikidata_ids=secondary_wikidata_ids,
                    custom_categories=custom_categories,
                    suffix=suffix
                )
                
                if texts is None: continue
                wikidata=texts['wikidata'] #if wikidata taken from gpkg file
                wikidata_list = list()
                wikidata_list.append(wikidata)
                wikidata_list += secondary_wikidata_ids

                
                wikidata_list_upperlevel = list()
                for wd in wikidata_list:
                    entity_list = modelwiki.wikidata2instanceof_list(wd)
                    if entity_list is not None:
                        wikidata_list_upperlevel += entity_list
                wikidata_list += wikidata_list_upperlevel
                del wikidata_list_upperlevel
                del entity_list


            elif desc_dict['mode'] == 'auto':
                desc_dict['model'] = modelwiki.wikidata_input2id(
                    desc_dict.get('model', None))
                # transfer street user input deeper, it can be vector file name
                desc_dict['street'] = desc_dict.get('street', None)

                desc_dict['city'] = modelwiki.wikidata_input2id(
                    desc_dict.get('city', None))
                desc_dict['line'] = modelwiki.wikidata_input2id(
                    desc_dict.get('line', None))

                
                texts = self.make_image_texts_vehicle(
                    filename=filename,
                    vehicle=desc_dict['vehicle'],
                    model=desc_dict.get('model', None),
                    street=desc_dict.get('street', None),
                    number=desc_dict.get('number', None),
                    digital_number=desc_dict.get('digital_number', None),
                    system=desc_dict.get('system', None),
                    route=desc_dict.get('route', None),
                    country=desc_dict.get('country', None),
                    line=desc_dict.get('line', None),
                    operator=desc_dict.get('operator', None),
                    operator_vehicle_category=desc_dict.get('operator_vehicle_category', None),
                    facing=desc_dict.get('facing', None),
                    colors=desc_dict.get('colors', None),
                    secondary_wikidata_ids=secondary_wikidata_ids,
                    custom_categories=custom_categories,
                    suffix=suffix
                )
                if texts is None:
                    # invalid metadata for this file, continue to next file
                    continue
                wikidata_list = list()
                wikidata_list += texts['structured_data_on_commons']
                wikidata_list += secondary_wikidata_ids
                
            elif desc_dict['mode'] == 'bus':
                desc_dict['model'] = modelwiki.wikidata_input2id(
                    desc_dict.get('model', None))
                # transfer street user input deeper, it can be vector file name
                desc_dict['street'] = desc_dict.get('street', None)

                desc_dict['city'] = modelwiki.wikidata_input2id(
                    desc_dict.get('city', None))
                desc_dict['line'] = modelwiki.wikidata_input2id(
                    desc_dict.get('line', None))

                
                texts = self.make_image_texts_vehicle(
                    filename=filename,
                    vehicle='bus',
                    model=desc_dict.get('model', None),
                    street=desc_dict.get('street', None),
                    number=desc_dict.get('number', None),
                    digital_number=desc_dict.get('digital_number', None),
                    system=desc_dict.get('system', None),
                    route=desc_dict.get('route', None),
                    country=desc_dict.get('country', None),
                    line=desc_dict.get('line', None),
                    operator=desc_dict.get('operator', None),
                    operator_vehicle_category=desc_dict.get('operator_vehicle_category', None),
                    facing=desc_dict.get('facing', None),
                    colors=desc_dict.get('colors', None),
                    secondary_wikidata_ids=secondary_wikidata_ids,
                    custom_categories=custom_categories,
                    suffix=suffix
                )
                if texts is None:
                    # invalid metadata for this file, continue to next file
                    continue
                wikidata_list = list()
                wikidata_list += texts['structured_data_on_commons']
                wikidata_list += secondary_wikidata_ids
                
            elif desc_dict['mode'] == 'vehicle':
                desc_dict['model'] = modelwiki.wikidata_input2id(
                    desc_dict.get('model', None))
                # transfer street user input deeper, it can be vector file name
                desc_dict['street'] = desc_dict.get('street', None)

                desc_dict['city'] = modelwiki.wikidata_input2id(
                    desc_dict.get('city', None))
                desc_dict['line'] = modelwiki.wikidata_input2id(
                    desc_dict.get('line', None))

                
                texts = self.make_image_texts_vehicle(
                    filename=filename,
                    vehicle=desc_dict['vehicle'],
                    model=desc_dict.get('model', None),
                    street=desc_dict.get('street', None),
                    number=desc_dict.get('number', None),
                    digital_number=desc_dict.get('digital_number', None),
                    system=desc_dict.get('system', None),
                    route=desc_dict.get('route', None),
                    country=desc_dict.get('country', None),
                    line=desc_dict.get('line', None),
                    operator=desc_dict.get('operator', None),
                    operator_vehicle_category=desc_dict.get('operator_vehicle_category', None),
                    facing=desc_dict.get('facing', None),
                    colors=desc_dict.get('colors', None),
                    secondary_wikidata_ids=secondary_wikidata_ids,
                    custom_categories=custom_categories,
                    suffix=suffix
                )
                if texts is None:
                    # invalid metadata for this file, continue to next file
                    continue
                wikidata_list = list()
                wikidata_list += texts['structured_data_on_commons']
                wikidata_list += secondary_wikidata_ids


   
            
            # HACK
            # UPLOAD WEBP instead of TIFF if tiff is big
            # if exists file with webp extension:
            filename_webp = filename.replace('.tif', '.webp')
            src_filesize_mb = os.path.getsize(filename) / (1024 * 1024)
            if filename.endswith(('.tif','.tiff')) and src_filesize_mb > self.tiff2webp_min_size_mb :
                print('file is big, convert to webp to bypass upload errors')
                self.convert_to_webp(filename)

            if filename.endswith(('.tif','.tiff')) and os.path.isfile(filename_webp):
                print(
                    'found tif and webp file with same name. upload webp with fileinfo from tif')
                if not dry_run:
                    self.move_file_to_uploaded_dir(
                        filename, uploaded_folder_path)
                filename = filename_webp
                texts["name"] = texts["name"].replace('.tif', '.webp').replace('.tiff', '.webp')
                
            if filename.lower().endswith(('.mp4','.mov','.avi')):
                video_converted_filename=self.convert_to_webm(filename)
            if filename.lower().endswith(('.mp4','.mov','.avi')) and os.path.isfile(video_converted_filename):
                print(
                    'found mp4 and webm file with same name. upload webm with fileinfo from mp4')
                if not dry_run:
                    self.move_file_to_uploaded_dir(
                        filename, uploaded_folder_path)
                filename = video_converted_filename
                texts["name"] = texts["name"].replace('.mp4', '.webm').replace('.MP4', '.webm').replace('.MOV', '.webm').replace('.mov', '.webm').replace('.avi', '.webm').replace('.AVI', '.webm')             
                

            print(texts["name"])
            print(texts["text"])
            
            

            #remove duplicates
            wikidata_list = list(dict.fromkeys(wikidata_list))
            while("" in wikidata_list):
                wikidata_list.remove("")
            
            #print wikidata entitines for append
            templist=list()
            for wdid in wikidata_list:
                wd = modelwiki.get_wikidata_simplified(wdid)
                templist.append('【'+wd['labels'].get('en','no en label')+'】')
            print('-'.join(templist))
            del templist

  
            if not dry_run:
                if '_replace' in filename:
                    #ignore_warning=True
                    
                    if '_reupload' in filename:
                        self.logger.info('replace file..')
                        modelwiki.replace_file_commons( modelwiki.pagename_from_id(self.get_replace_id_from_string(filename)),filename)

                    self.logger.info('You should manualy replace texts. Open https://commons.wikimedia.org/entity/M'+self.get_replace_id_from_string(filename))
                    print('Texts for manual update')
                    
                    txt = "{{Rename|"+texts["name"]+"|2|More detailed object name, taken from wikidata}}"
                    print(txt)
                    print(texts["text"])
                    input("Press Enter to continue...")
                    # CREATE CATEGORY PAGES
                    if len(texts['need_create_categories'])>0:
                        for ctd in texts['need_create_categories']:
                            if not modelwiki.is_category_exists(ctd['name']):
                                self.logger.info('creating category '+ctd['name'])
                            modelwiki.create_category(ctd['name'], ctd['content'])
                            

                    # move uploaded file to subfolder
                    if not dry_run:
                        self.move_file_to_uploaded_dir(
                            filename, uploaded_folder_path)

                    if progressbar_on:
                        pbar.update(1)
                
                    
                    continue
                else:
                    ignore_warning = False
                upload_messages = self.upload_file(
                    filename, texts["name"], 
                    texts["text"], 
                    verify_description=desc_dict['verify'],
                    ignore_warning = ignore_warning
                )

                print(upload_messages)



            self.logger.info('append claims')
            
            claims_append_result = modelwiki.append_image_descripts_claim(
                texts["name"], wikidata_list, dry_run)            
            claims_append_result = modelwiki.append_location_of_creation(
                texts["name"], texts["location_of_creation"], dry_run)
            if not dry_run:
                modelwiki.create_category_taken_on_day(
                    texts['country'].title(), texts['dt_obj'].strftime("%Y-%m-%d"))
            else:
                print('will append '+' '.join(wikidata_list))

            uploaded_paths.append(
                'https://commons.wikimedia.org/wiki/File:'+texts["name"].replace(' ', '_'))

            if claims_append_result is None:
                # UPLOAD FAILED
                if 'Uploaded file is a duplicate of' in upload_messages:
                    old_filename = self.get_old_filename_from_overwrite_error(upload_messages)
                    uploaded_folder_path_dublicate = uploaded_folder_path.replace(
                        'commons_uploaded', 'commons_duplicates')
                    self.move_file_to_uploaded_dir(
                        filename, uploaded_folder_path_dublicate)
                    
                    # write description to text file for panoramio-replace process
                    import pickle
                    photo_duplicate_desc={'old_filename':old_filename,
                                          'desc':texts["text"],
                                          'filename':os.path.join(uploaded_folder_path_dublicate,os.path.basename(filename)),
                                          'new_name':texts["name"],
                                          'wikidata_list':wikidata_list,
                                          'need_create_categories':texts['need_create_categories']}
                    photo_duplicate_desc_filename = os.path.join(uploaded_folder_path_dublicate,os.path.splitext(os.path.basename(filename))[0]+'.description')
                    file = open(photo_duplicate_desc_filename, 'wb')
                    pickle.dump(photo_duplicate_desc, file)
                    file.close()
                # Continue to next file
                #continue
            else:
                self.logger.info('check if replace old photo')
                # REPLACE old panoramio photo. New photo uploaded, server not triggered at dublicate:
                if '_replace' in filename:
                    
                    old_file_pageid = self.get_replace_id_from_string(filename)
                    old_file_pagename = modelwiki.pagename_from_id(old_file_pageid)
                    self.logger.info('add template for replace '+old_file_pagename)
                    modelwiki.file_add_duplicate_template(pagename=old_file_pagename,new_filename=texts["name"])


            # CREATE CATEGORY PAGES
            if len(texts['need_create_categories'])>0:
                for ctd in texts['need_create_categories']:
                    if not modelwiki.is_category_exists(ctd['name']):
                        self.logger.info('creating category '+ctd['name'])
                    modelwiki.create_category(ctd['name'], ctd['content'])
                    

            # move uploaded file to subfolder
            if not dry_run:
                self.move_file_to_uploaded_dir(
                    filename, uploaded_folder_path)

            if progressbar_on:
                pbar.update(1)

        if progressbar_on:
            pbar.close()
        if not dry_run:
            self.logger.info('uploaded: ')
        else:
            self.logger.info('emulating upload. URL will be: ')

        self.logger.info("\n".join(uploaded_paths))

       
                
                
                
                
    def get_old_filename_from_overwrite_error(self,upload_message:str)->str:
        '''
        from 'We got the following warning(s): duplicate: Uploaded file is a duplicate of ['Krasnogorsk-2013_-_panoramio_(320).jpg'].'
        return Krasnogorsk-2013_-_panoramio_(320).jpg
        
        '''

        import re
        test_str = upload_message
        regex = r"\['(.*?)'\]"
        matches = re.finditer(regex, test_str, re.MULTILINE)

        for matchNum, match in enumerate(matches, start=1):
            
            #print ("Match {matchNum} was found at {start}-{end}: {match}".format(matchNum = matchNum, start = match.start(), end = match.end(), match = match.group()))
            
            for groupNum in range(0, len(match.groups())):
                groupNum = groupNum + 1
                
                #print ("Group {groupNum} found at {start}-{end}: {group}".format(groupNum = groupNum, start = match.start(groupNum), end = match.end(groupNum), group = match.group(groupNum)))

                return match.group(groupNum)
        

    def convert_to_webm(self,filename)->str:
        # convert video to webm vp9. files not overwriten
        filename_dst = filename.replace('.mp4', '.webm').replace('.MP4', '.webm').replace('.MOV', '.webm').replace('.mov', '.webm').replace('.avi', '.webm').replace('.AVI', '.webm')    
        if os.path.isfile(filename_dst): return filename_dst
        
        file_stats = os.stat(filename)
        filesize_mb=file_stats.st_size / (1024 * 1024)
        if filesize_mb > 20:
        
            cmd = ['ffmpeg', '-i',filename, '-c:v', 'libvpx-vp9', '-b:v', '0', '-crf', '30', '-pass', '1', '-row-mt', '1', '-an', '-f', 'webm', '-y', '/dev/null']
            print(' '.join(cmd))
            response = subprocess.run(cmd)

            cmd = ['ffmpeg', '-i', filename, '-c:v', 'libvpx-vp9', '-b:v', '0', '-crf', '30', '-pass', '2', '-row-mt', '1', '-c:a', 'libopus',   filename_dst]
            print(' '.join(cmd))
            response = subprocess.run(cmd)
            return filename_dst
        else:
            self.logger.info('video file is small, convert lossless')
            cmd = ['ffmpeg', '-i', filename, '-c:v', 'libvpx-vp9', '-lossless', '1',  '-c:a', 'libopus',   filename_dst]
            print(' '.join(cmd))
            response = subprocess.run(cmd)
            return filename_dst
            
        
    def move_file_to_uploaded_dir(self, filename, uploaded_folder_path):
        # move uploaded file to subfolder
        if not os.path.exists(uploaded_folder_path):
            os.makedirs(uploaded_folder_path)
        shutil.move(filename, os.path.join(
            uploaded_folder_path, os.path.basename(filename)))
