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
import shutil
from tqdm import tqdm

class Fileprocessor:
    logging.basicConfig(
        level=logging.ERROR,
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
            use_filename=commons_name,  # keep original names of urls and files, otherwise it will ask to enter a name for each file
            keep_filename=True,  # Keep the filename as is
            # Ask for verification of the description
            verify_description=verify_description,
            targetSite=site,  # The site object for Wikimedia Commons
            aborts=True, #List of the warning types to abort upload on
            chunk_size=self.chunk_size,
        )
        print()
        print('=======================================================')
        print(commons_name.center(60,'*'))
        # Try to run the upload robot
        try:
            bot.run()
        except Exception as e:
            # Handle API errors
            print(f"API error: {e.code}: {e.info}")




    
    
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
            raise ValueError('object https://www.wikidata.org/wiki/' +
                              wikidata+' must has name ru and name en')
            

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





    def make_image_texts_vehicle(self, filename, vehicle, model, number, street=None, system=None,  route=None, country=None, line=None, facing=None, colors=None, secondary_wikidata_ids=None, digital_number=None) -> dict:
        assert os.path.isfile(filename)
        
        from model_wiki import Model_wiki  as Model_wiki_ask
        modelwiki = Model_wiki_ask()

        vehicle_names = {'ru': {'tram': 'трамвай', 'trolleybus': 'троллейбус',
                           'bus': 'автобус', 'train': 'поезд', 'locomotive':'локомотив', 'auto': 'автомобиль', 'plane': 'самолёт'}}
        wikidata_4_structured_data = list()
        
        #assert facing in ('Left','Right',None)

        # obtain exif
        dt_obj = self.image2datetime(filename)
        geo_dict = self.image2coords(filename)
        
        if model is not None:
            model_wdid = modelwiki.wikidata_input2id(model)
            model_wd = modelwiki.get_wikidata(model_wdid)
            model_names = model_wd["labels"]
            wikidata_4_structured_data.append(model_wd['id'])

        # STREET
        # if street - vector file path: get street wikidata code by point in polygon
        if street is not None:
            # take street from ogr vector file
            if os.path.isfile(street):
                if geo_dict is None: 
                    self.logger.error(filename + ' not set street, must have coordinates for search in geodata')
                    return None
                regions_filepath = street
                from model_geo import Model_Geo  as Model_geo_ask
                modelgeo = Model_geo_ask()
                street_wdid = modelgeo.identify_deodata(geo_dict.get("lat"),geo_dict.get("lon"),regions_filepath,'wikidata')
                if street_wdid is None: 
                    msg=str(geo_dict.get("lat"))+' '+str(geo_dict.get("lon"))
                    msg += ' file:'+regions_filepath
                    self.logger.error(filename + ' not found street in geodata, please set. '+msg+' Continue to next file')
                    return None
                street_wd = modelwiki.get_wikidata(street_wdid)
            else:
                # take street from user input
                street_wdid = modelwiki.wikidata_input2id(street)
                if street is not None: assert street_wdid is not None

            street_wd = modelwiki.get_wikidata(street_wdid)
            street_names = street_wd["labels"]
            wikidata_4_structured_data.append(street_wd['id'])
            #add city/district to structured data
            city_wd = modelwiki.get_territorial_entity(street_wd)
            wikidata_4_structured_data.append(city_wd['id'])
            
        # ROUTE
        if route is None:
            # extract route "34" from 3216_20070112_052_r34.jpg
            import re
            regex = "_r(.*?)[_.\b]"
            test_str=os.path.basename(filename)
            
            matches = re.finditer(regex, test_str, re.MULTILINE)
            for match in matches:
                route = match.group()[2:-1]
            if route=='z': route=None
                        
        # DIGITAL_NUMBER
        if digital_number is None:
            # extract number "1456" from 2TE10M-1456_20230122_444_dn1456.jpg
            import re
            regex = "_n(.*?)[_.\b]"
            test_str=os.path.basename(filename)
            
            matches = re.finditer(regex, test_str, re.MULTILINE)
            for match in matches:
                digital_number = match.group()[2:-1]
            
        # SYSTEM
        if system is not None:
            system_wdid = modelwiki.wikidata_input2id(system)
            system_wd = modelwiki.get_wikidata(system_wdid)

            system_names = system_wd["labels"]
            #GET "RZD" from "Russian Railways" 
            if 'P1813' in system_wd['claims']:
                for abbr_record in system_wd['claims']['P1813']:
                    system_names[abbr_record['value']['language']] = abbr_record['value']['text']
                    
            wikidata_4_structured_data.append(system_wd['id'])
            system_territorial_entity = modelwiki.get_territorial_entity(system_wd)
            if system_territorial_entity is not None:
                city_name_en = system_territorial_entity['labels']['en'] or ''
                city_name_ru = system_territorial_entity['labels']['ru'] or ''
            else:
                city_name_en = None
                city_name_ru = None

        elif system is None:

            city_wd = modelwiki.get_territorial_entity(street_wd)
            try:
                city_name_en = city_wd['labels']['en']
                city_name_ru = city_wd['labels']['ru']
            except:
                raise ValueError( 'object https://www.wikidata.org/wiki/' +
                              city_wd['id']+' must has name ru and name en')
            if city_wd['id'] not in wikidata_4_structured_data:
                wikidata_4_structured_data.append(city_wd['id'])
            

        # LINE
        line_wdid = None
        line_names = dict()
        if line is not None:
            line_wdid = self.take_user_wikidata_id(line)
            line_wd = modelwiki.get_wikidata(line_wdid)

            line_names = line_wd["labels"]

            wikidata_4_structured_data.append(line_wdid)
        elif line is None and vehicle in ('train','locomotive'):
            # GET RAILWAY LINE FROM WIKIDATA
            if 'P81' in street_wd['claims'] and len(street_wd['claims']['P81'])==1:
                line_wd=modelwiki.get_wikidata(street_wd['claims']['P81'][0]['value'])

        # trollybus garage numbers. extract 3213 from 3213_20060702_162.jpg
        if number == 'BEFORE_UNDERSCORE':
            number=os.path.basename(filename)[0:os.path.basename(filename).find('_')]
        
        filename_base = os.path.splitext(os.path.basename(filename))[0]
        filename_extension = os.path.splitext(os.path.basename(filename))[1]
        
        placenames={'ru':list(),'en':list()}
        
        if 'en' in line_names: 
            if len(line_names['en'])>0: placenames['en'].append(line_names['en'])
        if 'en' in street_names:
            if street_names['en'] != '': placenames['en'].append(street_names['en'])
                
        if vehicle not in ('train','locomotive'):
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
            commons_filename = '{city} {transport} {number} {dt} {place} {model}{extension}'.format(
            city=city_name_en,
            transport=vehicle,
            number=number,
            dt=dt_obj.strftime("%Y-%m %s"),
            place=' '.join(placenames['en']),
            model = model_names['en'],
            extension=filename_extension)
            
            

            #commons_filename = objectname_en + " " +dt_obj.strftime("%Y-%m %s") + model_names['en'] + ' '+ ' '.join(placenames['en'])+ ' ' + filename_extension
        elif vehicle in ('train','locomotive'):
            assert street_names is not None or line_names is not None
            if system_names['en']=='':system_names['en']=''
            if system_names['ru']=='':system_names['ru']=''
            
            #{model} removed


            objectname_en = '{system}{number}'.format(
                system=system_names['en']+' ',
                city=city_name_en,
                model=model_names['en'],
                number=translit(number, "ru", reversed=True),
                place=' '.join(placenames['en'])
            )
            commons_filename = '{system}{number} {dt} {place} {timestamp}{extension}'.format(
            system=system_names['en']+' ',
            number=translit(number, "ru", reversed=True),
            dt=dt_obj.strftime("%Y-%m"),
            place=' '.join(placenames['en']),
            timestamp=dt_obj.strftime("%s"),
            extension=filename_extension
            )
            
            objectname_ru = '{system}{number}'.format(
                system=system_names['ru']+' ',
                transport=vehicle_names['ru'][vehicle],
                model=model_names.get('ru', model_names['en']),
                number=number
            )       

        commons_filename = commons_filename.replace("/", " drob ")
        

        text = ''

        st = """== {{int:filedesc}} ==
{{Information
|description="""
        captions=dict()
        captions['en']=objectname_en + ' at ' + street_names['en']
        if route is not None:
            captions['en'] += ' Line '+route
        if line_wdid is not None:
            captions['en'] += ' '+modelwiki.get_wikidata(line_wdid)['labels']['en']
        st += "{{en|1=" +captions['en'] + '}}'
        
        captions['ru']=objectname_ru + ' на ' +  \
            street_names['ru'].replace(
                'Улица', 'улица').replace('Проспект', 'проспект')
        if route is not None:
            captions['ru'] += ' Маршрут '+route
        if line_wdid is not None:
            captions['ru'] += ' '+modelwiki.get_wikidata(line_wdid)['labels']['ru']
        st += "{{ru|1=" +captions['ru'] + '}}'
        
        if model is not None: st += " {{on Wikidata|" + model_wdid.split('#')[0] + "}}\n"
        st += " {{on Wikidata|" + street_wdid + "}}\n"
        
        if type(secondary_wikidata_ids) == list and len(secondary_wikidata_ids)>0:
            for wdid in secondary_wikidata_ids:
                st += " {{on Wikidata|" + wdid + "}}\n"
                heritage_id = None
                heritage_id = modelwiki.get_heritage_id(wdid)
                if heritage_id is not None:
                    st += "{{Cultural Heritage Russia|" + heritage_id + "}}"
                    today = datetime.today()
                    if today.strftime('%Y-%m') == '2023-09':
                        st += "{{Wiki Loves Monuments 2023|1=ru}}"
        
        st += "\n"
        st += (
            """|source={{own}}
|author={{Creator:Artem Svetlov}}
|date="""
            + "{{Taken on|"
            + dt_obj.isoformat()
            + "|location="
            + country
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
        transports_color = {
        'tram': 'Trams', 
        'trolleybus': 'Trolleybuses',
        'bus': 'Buses',
        'train': 'Rail vehicles',
        'locomotive': 'Rail vehicles',
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
        try:
            text = text + \
                "[[Category:" + street_wd["claims"]["P373"][0]["value"] + "]]" + "\n"
        except:
            pass
        text = text + "[[Category:Photographs by " + \
            self.photographer+'/'+country+'/'+transports[vehicle].lower()+"]]" + "\n"
        
        if 'line_wd' in locals() and line_wd is not None:
            text = text + \
                "[[Category:" + \
                line_wd["claims"]["P373"][0]["value"]+"]]" + "\n"

        # locale.setlocale(locale.LC_ALL, 'en_GB')
        if vehicle in ('train','locomotive'):
            text += "[[Category:Railway photographs taken on " + \
                dt_obj.strftime("%Y-%m-%d")+"]]" + "\n"
            if isinstance(country, str):
                text += "[[Category:" + \
                    dt_obj.strftime("%B %Y") + \
                    " in rail transport in "+country+"]]" + "\n"

        if vehicle == 'tram':
            text += "[[Category:Railway photographs taken on " + \
                dt_obj.strftime("%Y-%m-%d")+"]]" + "\n"
            if isinstance(country, str):
                text += "[[Category:" + \
                    dt_obj.strftime("%B %Y") + \
                    " in tram transport in "+country+"]]" + "\n"
                    
        #do not add facing category if this is interior
        if 'Q60998096' in secondary_wikidata_ids: facing=None
        if facing is not None:
            facing = facing.strip().capitalize()
            #assert facing.strip().upper() in ('LEFT','RIGHT')
            

            if facing == 'Left': text += "[[Category:"+transports[vehicle]+" facing " +  facing.lower() + "]]\n"
            if facing == 'Right': text += "[[Category:"+transports[vehicle]+" facing " +  facing.lower() + "]]\n"
            if facing == 'Side': text += "[[Category:Side views of "+transports[vehicle].lower()+"]]\n"
            if facing == 'Rear': text += "[[Category:Rear views of "+transports[vehicle].lower()+"]]\n"
            if facing == 'Front': text += "[[Category:Front views of "+transports[vehicle].lower()+"]]\n"
            if facing == 'Rear three-quarter'.capitalize(): text += "[[Category:Rear three-quarter views of "+transports[vehicle].lower()+"]]\n"
            if facing == 'Three-quarter'.capitalize(): text += "[[Category:Three-quarter views of "+transports[vehicle].lower()+"]]\n"
            
            if facing == 'Left': wikidata_4_structured_data.append('Q119570753')
            if facing == 'Right': wikidata_4_structured_data.append('Q119570670')
            if facing == 'Front': wikidata_4_structured_data.append('Q1972238')
        
        if colors is None and 'color' in  os.path.basename(filename):
            colors = self.get_colorlist_from_string(os.path.basename(filename))
        if colors is not None:        
            colorname = ''
            colors.sort()
            colorname = ' and '.join(colors)
            colorname = colorname.lower().capitalize()
            text += "[[Category:{colorname} {transports}]]\n".format(
            transports = transports_color[vehicle].lower(),
            colorname = colorname)
            
        
        #vehicle to wikidata
            vehicles_wikidata={"trolleybus":"Q5639","bus":"Q5638","tram":"Q3407658","auto":"Q1420","locomotive":"Q93301","train":"Q870"}
            if vehicle in vehicles_wikidata: wikidata_4_structured_data.append(vehicles_wikidata[vehicle])
        
        #number
        if number is not None:
            number_filtered = number
            if '-' in number_filtered: number_filtered=number_filtered[number_filtered.index('-')+1:]
            if digital_number is None:
                digital_number = number_filtered
        if number is not None and vehicle in ('locomotive','train'):
            text += "[[Category:Number "+digital_number+" on rail vehicles]]\n"
        elif number is not None and vehicle == 'bus':
            text += "[[Category:Number "+digital_number+" on buses]]\n"       
        elif number is not None and vehicle != 'tram':
            text += "[[Category:Number "+digital_number+" on vehicles]]\n"            
        if number is not None and vehicle == 'tram':
            text += "[[Category:Trams with fleet number "+digital_number+"]]\n"
        if dt_obj is not None:
            text += "[[Category:{transports} in {country} photographed in {year}]]\n".format(
            transports = transports[vehicle],
            country = country,
            year = dt_obj.strftime("%Y"),
            )
            
        # category for model. search for category like "ZIU-9 in Moscow"
        cat = modelwiki.get_category_object_in_location(model_wd['id'],street_wd['id'],order=digital_number,verbose=True)
        if cat is not None: 
            text = text + cat + "\n"
        else:
            text = text + \
                "[[Category:" + model_wd["claims"]["P373"][0]["value"] + '|'+ digital_number +"]]" + "\n"
        
        # categories for secondary_wikidata_ids
        # search for geography categories using street like (ZIU-9 in Russia)

        if type(secondary_wikidata_ids) == list and len(secondary_wikidata_ids)>0:
            for wdid in secondary_wikidata_ids:
                cat = modelwiki.get_category_object_in_location(wdid,street_wdid,verbose=True)
                if cat is not None: 
                    text = text + cat + "\n"
                else:
                    wd_record = modelwiki.get_wikidata_simplified(wdid)
                    if wd_record is None:
                        return None
                    secondary_objects_should_have_commonscat = False
                    if secondary_objects_should_have_commonscat:
                        assert 'commons' in wd_record, 'https://www.wikidata.org/wiki/'+wdid + ' must have commons'
                        assert wd_record["commons"] is not None, 'https://www.wikidata.org/wiki/'+wdid + ' must have commons'
                    
                    if 'commons' in wd_record and wd_record["commons"] is not None:
                        text = text + "[[Category:" + wd_record["commons"] + "]]" + "\n"
        
        return {"name": commons_filename, "text": text, 
        "structured_data_on_commons": wikidata_4_structured_data, 
        'captions':captions,
        "dt_obj": dt_obj}
    def get_colorlist_from_string(self,test_str:str)->list:
        #from string 2002_20031123__r32_colorgray_colorblue.jpg  returns [Gray,Blue]
        # 2002_20031123__r32_colorgray_colorblue.jpg
        
        import re
        #cut to . symbol if extsts
        test_str = test_str[0:test_str.index('.')]
        
        #split string by _
        parts = re.split('_+', test_str)
        
        lst = list()
        for part in parts:
            if part.startswith('color'):
                lst.append(part[5:].title())
        
        print(lst)
        return lst
       
    def get_wikidatalist_from_string(self,test_str:str)->list:
        #from string 2002_20031123__r32_colorgray_colorblue_wikidataQ12345_wikidataAntonovka.jpg  returns [Q12345,Antonovka]
        # 2002_20031123__r32_colorgray_colorblue.jpg
        
        import re
        #cut to . symbol if extsts
        test_str = test_str[0:test_str.index('.')]
        
        lst = re.findall(r'(Q\d+)', test_str)
        

        if len(lst)>0:
            self.logger.debug('from filename obtained wikidata:'+' '.join(lst))

        return lst
       
    
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
            today = datetime.today()
            if today.strftime('%Y-%m') == '2023-09':
                st += "{{Wiki Loves Monuments 2023|1=ru}}"
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

    def make_image_texts_standalone(self,filename,wikidata,secondary_wikidata_ids)->dict:
        from model_wiki import Model_wiki  as Model_wiki_ask
        modelwiki = Model_wiki_ask()
        
        wd_record = modelwiki.get_wikidata_simplified(wikidata)

        instance_of_data = list()
        if 'instance_of_list' in wd_record:
            for i in wd_record['instance_of_list']:
                instance_of_data.append(
                    modelwiki.get_wikidata_simplified(i['value']))
            
            
        objectnames = {}

        objectnames['en'] = wd_record['names']["en"]
        objectnames['ru'] = wd_record['names']["ru"]
        
        objectname_long_ru = ''
        objectname_long_en = ''
        if len(instance_of_data) > 0:
            objectname_long_ru = ', '.join(
                d['names']['ru'] for d in instance_of_data) + ' '+wd_record['names']["ru"]
            objectname_long_en = ', '.join(
                d['names']['en'] for d in instance_of_data) + ' '+wd_record['names']["en"]
        
        commons_filename = self.commons_filename(filename,objectnames,wikidata,dt_obj = self.image2datetime(filename))
        
        objects_wikidata = list()
        for obj_wdid in secondary_wikidata_ids:
            obj_wdid = self.take_user_wikidata_id(obj_wdid)
            obj_wd = modelwiki.get_wikidata(obj_wdid)
            objects_wikidata.append(obj_wd)
        for obj_wd in objects_wikidata:
            try:
                objectname_long_ru = objectname_long_ru + ', '+ obj_wd['labels']['ru']
                objectname_long_en = objectname_long_en + ', '+ obj_wd['labels']['en']
            except:
                raise ValueError('object https://www.wikidata.org/wiki/' +
                              obj_wd['id']+' must has name ru and name en')


        j = {'new_filename':commons_filename,'ru':objectname_long_ru,'en':objectname_long_en}
        return j
    
    def copy_image4standalone(self,filename,new_filename):
        images_dir = '2standalone'
        if not os.path.isdir(images_dir):
            os.makedirs(images_dir)
        new_filename = os.path.join(images_dir,new_filename)
        shutil.copy2(filename,new_filename)
        
    def create_json4standalone(self,filename,commons_filename, text_ru, text_en):
        images_dir = '2standalone'
        if not os.path.isdir(images_dir):
            os.makedirs(images_dir)
        new_filename = os.path.join(images_dir,commons_filename)
        j = dict()
        j['caption']=text_ru
        j['caption_en']=text_en
        j['hotlink_commons'] = 'https://commons.wikimedia.org/wiki/File:'+commons_filename
        json_filename = os.path.splitext(new_filename)[0]+'.json'
        with open(json_filename, 'w') as fp:
            json.dump(j, fp)
            
        
    def make_image_texts_simple(
        self, filename, wikidata, country='', rail='', secondary_wikidata_ids=list(),quick=False
    ) -> dict:
        # return file description texts
        # there is no excact 'city' in wikidata, use manual input cityname

        from model_wiki import Model_wiki  as Model_wiki_ask
        modelwiki = Model_wiki_ask()
    
        assert os.path.isfile(filename), 'not found '+filename

        # obtain exif
        if not quick:
            dt_obj = self.image2datetime(filename)
            geo_dict = self.image2coords(filename)
        else:
            dt_obj = datetime.strptime('1970:01:01 00:00:00', "%Y:%m:%d %H:%M:%S")
            geo_dict = None

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
        heritage_id = modelwiki.get_heritage_id(wikidata)
        if heritage_id is not None:
            st += "{{Cultural Heritage Russia|" + heritage_id + "}}"
            today = datetime.today()
            if today.strftime('%Y-%m') == '2023-09':
                st += "{{Wiki Loves Monuments 2023|1=ru}}"
        st += " {{ on Wikidata|" + wikidata + "}}"
        st += "\n"
        st += self.get_date_information_part(dt_obj, country)

        st += "}}\n"

        text += st

        if not quick:
            text = text + self.get_tech_templates(filename, geo_dict, country)
        else:
            text = text + " >>>>> TECH TEMPLATES SKIPPED <<<<<<\n"
        if rail:
            text += "[[Category:Railway photographs taken on " + \
                dt_obj.strftime("%Y-%m-%d")+"]]" + "\n"
            if isinstance(country, str) and len(country) > 3:
                text += "[[Category:" + \
                    dt_obj.strftime("%B %Y") + \
                    " in rail transport in "+country+"]]" + "\n"


        assert 'commons' in wd_record, 'https://www.wikidata.org/wiki/'+wikidata + ' must have commons'
        assert wd_record["commons"] is not None, 'https://www.wikidata.org/wiki/'+wikidata + ' must have commons'
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
                    assert wd_record["commons"] is not None, 'https://www.wikidata.org/wiki/'+wdid + ' must have commons'
                    text = text + "[[Category:" + wd_record["commons"] + "]]" + "\n"
        commons_filename = self.commons_filename(filename,objectnames,wikidata,dt_obj)
        
        return {"name": commons_filename, "text": text, "dt_obj": dt_obj}

    def commons_filename(self,filename,objectnames,wikidata,dt_obj)->str:
        # file name on commons
        
        from model_wiki import Model_wiki  as Model_wiki_ask
        modelwiki = Model_wiki_ask()
        
        filename_base = os.path.splitext(os.path.basename(filename))[0]
        filename_extension = os.path.splitext(os.path.basename(filename))[1]
        #if this is building: try get machine-reading address from https://www.wikidata.org/wiki/Property:P669
        building_info = modelwiki.get_building_record_wikidata(wikidata,stop_on_error=False)
        if building_info is not None:

            objectnames['en'] = (
            building_info["addr:street:en"]
            + " "
            + building_info["addr:housenumber:en"]
            )
        

        
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
            obj_wd = modelwiki.get_wikidata(obj_wdid)
            objects_wikidata.append(obj_wd)

        if self.is_wikidata_id(city):
            city_wdid = city
        else:
            city_wdid = self.search_wikidata_by_string(
                city, stop_on_error=True)
        city_wd = modelwiki.get_wikidata(city_wdid)

        # get country, only actual values. key --all returns historical values
        cmd = ['wd', 'claims', city_wdid, 'P17', '--json']
        response = subprocess.run(cmd, capture_output=True)
        country_json = json.loads(response.stdout.decode())
        country_wdid = country_json[0]
        country_wd = modelwiki.get_wikidata(country_wdid)

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

                if image_exif.get("fnumber", '') != "" and image_exif.get("fnumber", '') != "":
                    st += '|Aperture = f/' + str(image_exif.get("fnumber"))
                if image_exif.get("'focallengthin35mmformat'", '') != "" and image_exif.get("'focallengthin35mmformat'", '') != "":
                    st += '|Focal length 35mm = f/' + \
                        str(image_exif.get("'focallengthin35mmformat'"))
                st += '}}' + "\n"

                cameramodels_dict = {
                    'Pentax corporation PENTAX K10D': 'Pentax K10D',
                    'Pentax PENTAX K-r': 'Pentax K-r',
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

                # lens quess
                lens_detected = ''
                if image_exif.get("lensmodel", '') != "" and image_exif.get("lensmodel", '') != "": lens_detected = image_exif.get("lensmodel")
                
                self.logger.info('detected lens'+lens_detected)

                
                
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
        if path.lower().endswith('.stl'): return True
        cmd = [self.exiftool_path, path, "-datetimeoriginal", "-csv"]
        process = subprocess.run(cmd)

        if process.returncode == 0:
            return True
        else:
            return False

    def image2datetime(self, path):

        with open(path, "rb") as image_file:
            if not path.lower().endswith('.stl'):
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
            elif path.lower().endswith('.stl'):
                dt_obj = None

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

        for prop in item.claims:
            for statement in item.claims[prop]:
                if isinstance(statement.target, pywikibot.page._wikibase.ItemPage):
                    print(prop, statement.target.id,
                          statement.target.labels.get("en"))
                else:
                    print(prop, statement.target)



    def append_structured_data0(self, commonsfilename):
        commonsfilename = self.prepare_commonsfilename(commonsfilename)
        commons_site = pywikibot.Site("commons", "commons")

        # File to test and work with

        page = pywikibot.FilePage(commons_site, commonsfilename)
        repo = commons_site.data_repository()

        # Retrieve Wikibase data
        item = page.data_item()
        item.get()


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


    
    def process_and_upload_file(self,filepath,desc_dict):
        from model_wiki import Model_wiki
        modelwiki = Model_wiki()
        if not os.path.exists(filepath):
            print(filepath.ljust(50)+' '+' not exist')
            quit()
        assert os.path.exists(filepath)
        assert desc_dict['mode'] in ['object','vehicle','building']

        assert 'country' in desc_dict
        
        if not 'secondary_objects' in desc_dict: desc_dict['secondary_objects']=list() #for simple call next function
        if not 'dry_run' in desc_dict: desc_dict['dry_run']=False #for simple call next function
        if not 'later' in desc_dict: desc_dict['later']=False #for simple call next function
        if not 'verify' in desc_dict: desc_dict['verify']=False #for simple call next function
        if 'country' in desc_dict:
            desc_dict['country'] = desc_dict['country'].capitalize()
        else:
            desc_dict['country'] = None
        
        files, uploaded_folder_path = self.input2filelist(filepath)

        if len(files)==0:
            print(filepath+' all files already uploaded')
            quit()

        
        dry_run = desc_dict['dry_run']
        if desc_dict['later']==True: dry_run = True

        uploaded_paths = list()

        #count for progressbar
        total_files=0
        for filename in files:
            print(filename)
            if 'commons_uploaded' in filename: 
                continue
            if self.check_exif_valid(filename) :
                total_files = total_files + 1
                    
        progressbar_on = False
        if total_files>1 and 'progress' in desc_dict:
            progressbar_on = True
            pbar = tqdm(total=total_files)
        
        for filename in files:
            if 'commons_uploaded' in filename: continue
            if self.check_exif_valid(filename) :

                secondary_wikidata_ids = modelwiki.input2list_wikidata(desc_dict['secondary_objects'])
                

                #get wikidata from filepath

                if secondary_wikidata_ids == [] and 'Q' in filename:
                    secondary_wikidata_ids = self.get_wikidatalist_from_string(filename)

                if desc_dict['mode'] == 'object':
                    if desc_dict['wikidata'] == 'FROMFILENAME':
                        wikidata = self.get_wikidatalist_from_string(filename)[0]
                        del secondary_wikidata_ids[0]
                    else:
                        wikidata = modelwiki.wikidata_input2id(desc_dict['wikidata'])
                    
                    texts = self.make_image_texts_simple(
                        filename=filename,
                        wikidata=wikidata,
                        country=desc_dict['country'],
                        rail=desc_dict['rail'],
                        secondary_wikidata_ids = secondary_wikidata_ids,
                        quick=desc_dict['later']
                    )    
                    wikidata_list = list()
                    wikidata_list.append(wikidata)
                    wikidata_list += secondary_wikidata_ids
                    standalone_captions_dict = self.make_image_texts_standalone(filename,wikidata,secondary_wikidata_ids)
                    
                elif desc_dict['mode'] == 'vehicle':
                    desc_dict['model'] = modelwiki.wikidata_input2id(desc_dict.get('model',None))
                    #transfer street user input deeper, it can be vector file name
                    desc_dict['street'] = desc_dict.get('street',None)
                    desc_dict['system'] = modelwiki.wikidata_input2id(desc_dict.get('system',None))
                    desc_dict['city'] = modelwiki.wikidata_input2id(desc_dict.get('city',None))
                    desc_dict['line'] = modelwiki.wikidata_input2id(desc_dict.get('line',None))
                    desc_dict['line'] = modelwiki.wikidata_input2id(desc_dict.get('line',None))
                                    
                    texts = self.make_image_texts_vehicle(
                        filename=filename,
                        vehicle = desc_dict['vehicle'],
                        model = desc_dict.get('model',None),
                        street = desc_dict.get('street',None),
                        number = desc_dict.get('number',None),
                        digital_number = desc_dict.get('digital_number',None),
                        system = desc_dict.get('system',None),
                        route = desc_dict.get('route',None),
                        country = desc_dict.get('country',None),
                        line = desc_dict.get('line',None),
                        facing = desc_dict.get('facing',None),
                        colors = desc_dict.get('colors',None),
                        secondary_wikidata_ids = secondary_wikidata_ids
                    )  
                    if texts is None:
                        #invalid metadata for this file, continue to next file
                        continue
                    wikidata_list = list()
                    wikidata_list += texts['structured_data_on_commons']
                    wikidata_list += secondary_wikidata_ids
                    standalone_captions_dict = {'new_filename':texts['name'],'ru':texts['captions']['ru'],'en':texts['captions']['en']}

                    '''
                     'new_filename':commons_filename,'ru':objectname_long_ru,'en':objectname_long_en
                    '''


                if dry_run:
                    print()
                    print(texts["name"])
                    print(texts["text"])
                
                
                if not dry_run:
                    self.upload_file(
                        filename, texts["name"], texts["text"], verify_description=desc_dict['verify']
                    )
                    
                    #copy uploaded file to standalone-sources dir
                    
                    self.copy_image4standalone(filename,standalone_captions_dict['new_filename'])
                    self.create_json4standalone(filename,standalone_captions_dict['new_filename'],standalone_captions_dict['ru'],standalone_captions_dict['en'])
                    
                self.logger.info('append claims')
                claims_append_result = modelwiki.append_image_descripts_claim(texts["name"], wikidata_list, dry_run)
                if not dry_run:
                    modelwiki.create_category_taken_on_day(desc_dict['country'].capitalize(),texts['dt_obj'].strftime("%Y-%m-%d"))
                else:
                    print('will append '+' '.join(wikidata_list))
                    
                uploaded_paths.append('https://commons.wikimedia.org/wiki/File:'+texts["name"].replace(' ', '_'))
                
                if claims_append_result is None:
                    continue
                #move uploaded file to subfolder
                if not dry_run:
                    if not os.path.exists(uploaded_folder_path):
                        os.makedirs(uploaded_folder_path)
                    shutil.move(filename, os.path.join(uploaded_folder_path, os.path.basename(filename)))
           
                if progressbar_on: pbar.update(1)    
            else:
                print('can not open file '+filename+', skipped')
                continue
        if progressbar_on: pbar.close() 
        if not dry_run:
            print('uploaded: ')
        else:
            print('emulating upload. URL will be: ')

        print("\n".join(uploaded_paths))
        
        #add to job queue if not uploading now
        if dry_run:
            if not desc_dict['later']:
                add_queue = input("Add to queue? Y/N    ")
            else:
                add_queue='Y'
            
            #make call string
            if add_queue.upper()!='Y':
                print('not adding to queue')
                return
            
            if desc_dict['mode'] == 'object':
                cmd = 'python3 upload.py '
                cmd += wikidata + ' '
                cmd += '"'+filepath + '" '

            if desc_dict['mode'] == 'vehicle':
                cmd = 'python3 vehicle-upload.py '
                cmd += '"'+filepath + '" '
                cmd += '--vehicle "'+ desc_dict['vehicle'] + '" '
                if desc_dict['system']: cmd += '--system "'+ desc_dict['system'] + '" '
                if desc_dict['city']: cmd += '--city "'+ desc_dict['city'] + '" '
                if desc_dict['model']: cmd += '--model "'+ desc_dict['model'] + '" '
                if desc_dict['street']: cmd += '--street "'+ desc_dict['street'] + '" '
                if desc_dict['number']: cmd += '--number "'+ desc_dict['number'] + '" '
                if desc_dict['route']: cmd += '--route "'+ desc_dict['route'] + '" '
                if desc_dict['line']: cmd += '--line "'+ desc_dict['line'] + '" '
                if desc_dict['facing']: cmd += '--facing "'+ desc_dict['facing'] + '" '
                if desc_dict['colors']: cmd += '--colors '+ ' '.join(desc_dict['colors']) + ' '
                
            if desc_dict['country']: cmd += '--country "'+ desc_dict['country'] + '" '
            if len(secondary_wikidata_ids)>0: cmd += '-s ' + ' '.join(secondary_wikidata_ids)
                
           
            print('adding to queue')
            print(cmd)
            with open("queue.sh", "a") as file_object:
                file_object.write(cmd+"\n")
