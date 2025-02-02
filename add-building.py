#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os, subprocess, logging, argparse, sys
import shortuuid

import trolleway_commons
from model_wiki import Model_wiki

sample_expression ='''

'python3 add-building.py --building ' ||"building"|| ' --coords "' ||  round(y(point_on_surface(@geometry)),5) || ' ' || round(x(point_on_surface(@geometry)),5)|| '" --city   --street '||  "osm — lines_wikidata"  ||' -n "'||  "addr_housenumber" || '" --coord_source osm ' 

'''

parser = argparse.ArgumentParser(
    description="Create building entity in Wikidata and Wikimedia Commons "+''' 
    useful maps:
    get coords https://wikivoyage.toolforge.org/w/geomap.php?lang=ru
    dates https://flatinfo.ru/h_info1.asp?hid=189602
    wikidata objects https://wikishootme.toolforge.org/#lat=55.77&lng=37.66&zoom=18
    
    
    '''+ "\n expression for qgis \n"+sample_expression + "\\ \n\n   python3 add-building.py --building apartments --city Orekhovo-Zuevo --coord_source osm  --coords 55.80474,38.9689 --levels 3 --street Q122859896 --housenumber 9" + "python3 add-building.py --snow-fix --wikidata Q113682558 --city Torzhok"
)

'''
Run docker with this script one-off, for call from QGIS action:

cmd = docker run --rm -v "C:\trolleway\placejpg\:/opt/commons-uploader" -it placejpg:2023.11 ./add-building.py --help



QgsMessageLog.logMessage("Your plugin code has been executed correctly", 'MyPlugin', level=Qgis.Info)


anyway qgis can not start docker run
'''

parser.add_argument('--wikidata', type=str, required=False, help='Wikidata object optional')
parser.add_argument('--building', type=str, required=False,default=None, help='building type wkidata entity. Can be wikidata id, wikidata url, wikidata name')
parser.add_argument('--city', type=str, required=False, default=None, help='City wikidata entity. When not set, will be searched in "administrative entity" in wikidata. Can be wikidata id, wikidata url, wikidata name')
parser.add_argument('--district', type=str, required=False, help='Administrative entity wikidata entity. Can be wikidata id, wikidata url, wikidata name')
parser.add_argument('--project', type=str, required=False, help='project wikidata entity. Can be wikidata id, wikidata url, wikidata name')

parser.add_argument('--street', type=str, required='wikidata'  in sys.argv, help='Street wikidata entity. Can be wikidata id, wikidata url, wikidata name')
parser.add_argument('-n','--housenumber', type=str, required='wikidata'  in sys.argv, help='housenumber')
parser.add_argument('-c','--coords', type=str, required='wikidata' in sys.argv, help='latlong string in EPSG:4326. Separators: " ", | ,')
parser.add_argument('-cs','--coord_source', type=str, required='wikidata'  in sys.argv, choices=['osm','yandex maps','reforma'], help='internet project - source of coordinates')
parser.add_argument('--levels', type=int, required=False, help='Building levels count')
parser.add_argument('--levels_url', type=str, required=False, help='url for building levels refrence')
parser.add_argument('--year', type=int, required=False, help='year built')
parser.add_argument('--year_url', type=str, required=False, help='url for year refrence')
parser.add_argument('--architect', type=str, required=False, help='Architect. Can be wikidata id, wikidata url, wikidata name')
parser.add_argument('--architecture', type=str, required=False, help='Architecture style. Can be wikidata id, wikidata url, wikidata name')
parser.add_argument('--skip-en', action="store_const", const=True, required=False, help='do not change english label')


parser.add_argument('--wikidata-only', action="store_const", const=True, required=False, help='Create only wikidata entity, do not create commons category ')
parser.add_argument('--prepend-names', action="store_const", const=True, required=False, help='append original wikidata names at snow-fix ')
parser.add_argument('--category', type=str, default=None, required=False, help='Commons category. If already exist - script will create wikidata entity and links with this category')

parser.add_argument('--snow-fix', action="store_const", const=True, required=False, help='generate wikidata building name and description from LOCATED ON STREET attribure, then create commons category')

parser.add_argument(
    "-dry", "--dry-run", action="store_const", required=False, default=False, const=True
)

args = parser.parse_args()


if args.wikidata is None:
    # generate UUID as early as possible 
    local_wikidata_uuid='UUID'+str(shortuuid.uuid())
    print(f'Created UUID, you now can use it as placeholder for wikidata id place in filename')
    print(local_wikidata_uuid)
else:
    local_wikidata_uuid = None

if args.prepend_names and args.snow_fix==False:
    parser.error("--prepend_names work only with --snow_fix")
processor = trolleway_commons.CommonsOps()
modelwiki = Model_wiki()

city = args.city
dry_run = args.dry_run
city_wdid = args.city
building_wdid = args.building
# --- move to method

city_wdid = modelwiki.wikidata_input2id(city_wdid)

if args.snow_fix is not None:
    assert args.wikidata is not None
    building_wikidata = modelwiki.wikidata_input2id(args.wikidata)
    if city_wdid is None: city_wdid = modelwiki.get_settlement_for_object(building_wikidata)
    if city_wdid is None: raise ValueError(f'can not find city for https://www.wikidata.org/wiki/{building_wikidata}')
    if args.street is not None and args.housenumber is not None: 
        street_wdid = modelwiki.wikidata_input2id(args.street)
        modelwiki.wikidata_set_address(building_wikidata,street_wdid,housenumber=args.housenumber)
        
    modelwiki.wikidata_set_building_entity_name(building_wikidata,city_wdid=city_wdid,skip_en=args.skip_en)
    

    if not args.wikidata_only:
        
        category_name = modelwiki.create_building_category(building_wikidata, city_wikidata=city_wdid, dry_mode=dry_run)
    quit()
    
elif args.wikidata is not None:
    # create building category

    building_wikidata = modelwiki.wikidata_input2id(args.wikidata)
    if city_wdid is None: city_wdid = modelwiki.get_settlement_for_object(building_wikidata)
    if city_wdid is None: raise ValueError(f'can not find city for https://www.wikidata.org/wiki/{building_wikidata}')

    category_name = modelwiki.create_building_category(
            building_wikidata, city_wikidata=city_wdid, dry_mode=dry_run)
    if dry_run: 
        print('dry run. For object https://www.wikidata.org/wiki/'+building_wikidata)
        print('Proposed category name: https://commons.wikimedia.org/wiki/Category:'+category_name.replace(' ','_'))
        quit()

    print('Created https://www.wikidata.org/wiki/'+building_wikidata)
    print('Created https://commons.wikimedia.org/wiki/Category:'+category_name.replace(' ','_'))

    quit()
    
else:    
    # create new building in wikidata

    if building_wdid is not None:
        building_wdid = modelwiki.wikidata_input2id(str(building_wdid).strip()) 

    street_wdid = modelwiki.wikidata_input2id(str(args.street).strip())    
    if city_wdid is None: 
        city_wdid = modelwiki.get_settlement_for_object(street_wdid)
        if city_wdid is None: raise ValueError(f'can not find city for https://www.wikidata.org/wiki/{building_wikidata}') 
    assert city_wdid is not None   
    buildings = list()
    building = {
            "housenumber": str(args.housenumber),
            "building": building_wdid,
            "street_wikidata":street_wdid ,
            "latlonstr": args.coords,
            "coord_source": args.coord_source,
            'city':city_wdid,
            }
    if args.levels: building['levels'] = args.levels            
    if args.levels_url: building['levels_url'] = args.levels_url               
    if args.year: building['year'] = args.year            
    if args.year_url: building['year_url'] = args.year_url     
    if args.category: building['category'] = args.category.strip()         
    if args.district: building['district_wikidata'] = modelwiki.wikidata_input2id(str(args.district).strip())
    if args.project: building['project'] = modelwiki.wikidata_input2id(str(args.project).strip())
    if args.architect: building['architect'] = modelwiki.wikidata_input2id(str(args.architect).strip())
    if args.architecture: building['architecture'] = modelwiki.wikidata_input2id(str(args.architecture).strip())

    buildings.append(building)
    del building

    validation_pass = True
    for building in buildings:
        if modelwiki.validate_street_in_building_record(building) == False:
            validation_pass = False
    print('validation ok')

    if not validation_pass:
        print("street wikidata objects non valid")
        quit()
    category_name = ''
    for data in buildings:
        building_wikidata = modelwiki.create_wikidata_building(data, dry_mode=dry_run, local_wikidata_uuid=local_wikidata_uuid)
        if not args.wikidata_only and args.category is None:
            category_name = modelwiki.create_building_category(
                building_wikidata, city_wikidata=city_wdid, dry_mode=dry_run)

    # end of method    
    if args.dry_run:
        quit()
        
    print('Created https://www.wikidata.org/wiki/'+building_wikidata)
    print(building_wikidata)
    if not args.wikidata_only and category_name!='': 
        print('Created https://commons.wikimedia.org/wiki/Category:'+category_name.replace(' ','_'))
