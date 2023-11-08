# placejpg
python docker/termux script for upload to wikimedia commons photos of places, buildings and vehicles

Automation script for upload my photo collection to Wikimedia Commons. Commons categories, generate image descriptions based on Wikidata and EXIF. 
Limited to process images of buildings and vehicles. 

## Usage

### Simple usage

```
python3 upload.py  --location "United States" "Hollywood Boulevard"  i/imgfolder
# Uploads files from i/imgfolder to Wikimedia Commons. Search in Wikidata for "Hollywood Boulevard", use Commons Category for this object. Append template {{Taken on|yyyy-mm-dd|location=United States}}

python3 upload.py Q382500 --location Russia --later  i/imgfolder
# add to queue.sh command for Uploads files from i/imgfolder to Wikimedia Commons. Use Wikidata object Q382500, use Commons Category for this object. Append template {{Taken on|yyyy-mm-dd|location=Russia}}

```
### Advanced usage
```
python3 upload.py FROMFILENAME --location Russia   i/imgfolder/Q123456_101_20230203_001_Q666_Q777.jpg
# Upload file/folder to commons category of wikidata object Q123456. If this is a some geographic region, like city district, will search for needed categories for Q666 and Q777 entities.

python3 upload.py railway.gpkg --location Russia   i/imgfolder
# Upload file/folder, make spatial intersect of photo EXIF coordinates to vector polygons in file railway.gpkg, use it 'wikidata' field to determine object
```

## Install

### Install in Windows/Linux
1. Install Docker

2. Build image
```
git clone https://github.com/trolleway/placejpg.git
cd placejpg 
docker build --tag placejpg:2023.11 .

docker run --rm -v "${PWD}:/opt/commons-uploader" -it placejpg:2023.11
cp config.example.py config.py 


# Open config.py in text editor, set author names
nano user-config.py
```

Run
```bash
docker run --rm -v "${PWD}:/opt/commons-uploader"  -it placejpg:2023.11
```

## Used EXIF/IPTC image params

* GPS coordinates
* DateTime
* GPS Dest coordinates optional
* Make optional
* Model optional
* Lens model optional
* F number optional
* focal length in 35mm format optional




# Advanced tools

Create building and upload files from directory i/21
```
./add-building.py --street "Волжский бульвар" --housenumber "21" --coords "55.70592 37.74983" -cs osm --levels 5 --levels_url https://www.reformagkh.ru/myhouse/profile/view/8113254 --year 1962 --year_url https://www.reformagkh.ru/myhouse/profile/view/8113254 --photos i/21 #г. Москва, б-р. Волжский, д. 21
```

## Create building in Wkimedia Commons from OSM data in QGIS

1. Download Overpasss data
2. Use expression for generate command

'./add-building.py --street "'|| "addr:street" || '" --housenumber "'|| "addr:housenumber" || '" --coords "' ||round(y(point_on_surface( @geometry)),4) || ' ' || round(x(point_on_surface( @geometry)),4) ||'" -cs osm --levels '||"building:levels" || ' --photos "i/'|| replace("addr:housenumber",'/','_')||'"' 




