

python3 upload.py FROMFILENAME i/FROMFILENAME --country countries.gpkg --progress
python3 upload.py FROMFILENAME i/FROMFILENAME_RAIL --country countries.gpkg --rail --progress
python3 upload.py rail.gpkg i/RAIL_USEGPKG --country countries.gpkg --progress --rail
python3 upload.py poly.gpkg i/USEGPKG --country countries.gpkg --progress
python3 upload.py trolleybus.gpkg i/FROMSTREET --country countries.gpkg --progress

exit 0
python3 upload.py FROMFILENAME i/FROMFILENAME_RUSSIA --country Russia --progress
python3 upload.py FROMFILENAME i/FROMFILENAME_MOSCOW --country Moscow --progress
python3 upload.py FROMFILENAME i/FROMFILENAME_MOSCOW_RAIL --country Moscow --rail  --progress
python3 upload.py FROMFILENAME i/FROMFILENAME_MOSCOW_OBLAST --country "Moscow Oblast" --progress
python3 upload.py FROMFILENAME i/FROMFILENAME_MOSCOW_OBLAST_RAIL --country "Moscow Oblast" --rail --progress
python3 upload.py rail.gpkg i/FROMFILENAME_MOSCOW_OBLAST_RAIL_USEGPKG --country "Moscow Oblast" --rail --progress
python3 upload.py rail.gpkg i/FROMFILENAME_MOSCOW_RAIL_USEGPKG --country "Moscow" --rail --progress
python3 upload.py rail.gpkg i/SPB_RAIL --country "Saint Petersburg" --rail --progress
python3 upload.py FROMFILENAME i/FROMFILENAME_RUSSIA_RAIL --country Russia --rail --progress
python3 upload.py poly.gpkg i/FROMFILENAME_MOSCOW_OBLAST_USEGPKG --country "Moscow Oblast" --progress
python3 upload.py poly.gpkg i/MOSCOW_polygpkg --country "Moscow"  --progress
python3 upload.py poly.gpkg i/MOSCOW-OBLAST_polygpkg --country "Moscow Oblast" --progress
python3 upload.py poly.gpkg i/SPB_polygpkg --country "Saint Petersburg" --progress
python3 upload.py trolleybus.gpkg i/SPB_street --country "Saint Petersburg" --progress
python3 upload.py FROMFILENAME i/FROMFILENAME_BEL --country Belarus --progress
python3 upload.py poly.gpkg "i/Leningrad Oblast poly" --country "Leningrad Oblast" --progress
