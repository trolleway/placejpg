

python3 upload.py FROMFILENAME i/FROMFILENAME --country countries.gpkg --progress
python3 upload.py FROMFILENAME i/FROMFILENAME_RAIL --country countries.gpkg --rail --progress
python3 upload.py rail.gpkg i/RAIL_USEGPKG --country countries.gpkg --progress --rail
python3 upload.py poly.gpkg i/USEGPKG --country countries.gpkg --progress
python3 upload.py trolleybus.gpkg i/FROMSTREET --country countries.gpkg --progress
python3 upload.py trolleybus.gpkg i/FROMSTREET_RAIL --country countries.gpkg --progress --rail
python3 upload.py FROMFILENAME i/FROMFILENAME_mapillary --country countries.gpkg --progress
python3 upload.py FROMFILENAME i/FROMFILENAME/later --country countries.gpkg --progress