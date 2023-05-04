# commons-uploader
python docker/termux script for upload to wikimedia commons photos of buildings and vehicles

Automation script for upload my photo collection to Wikimedia Commons. Automatic create Wikidata objects, Commons categories, generate image descriptions based on Wikidata and EXIF. 
Limited to process images of buildings and vehicles. 

## Install

### Install in Windows/Linux
1. Install Docker

2. Build image
```
git clone https://github.com/trolleway/commons-uploader.git
cd commons-uploader 
docker build --tag commons-uploader:1.0 .

docker run --rm -v "${PWD}:/opt/commons-uploader" -v "${PWD}/wikibase-cli:/root/.config/wikibase-cli" -v "${PWD}/wikibase-cache:/root/.cache/wikibase-cli" -it commons-uploader:1.0
cp user-config.example.py user-config.py 


#Open user-config.py in text editor, set your Wikimedia Username in usernames['commons']['commons'] = 
nano user-config.py
chmod o-w  user-config.py
wb config instance https://www.wikidata.org
```

Run
```
docker run --rm -v "${PWD}:/opt/commons-uploader" -v "${PWD}/wikibase-cli:/root/.config/wikibase-cli" -v "${PWD}/wikibase-cache:/root/.cache/wikibase-cli" -it commons-uploader:1.0



# emulate upload files for building https://www.wikidata.org/wiki/Q118113014 witch has wikimedia commons category from directiry i
./building-upload.py https://www.wikidata.org/wiki/Q118113014 i --dry
```
The wikibase-cli volumes used by wikibase-cli tool for auth storage

### Install in Android / termux

```
pkg install git
git clone --depth 1 https://github.com/trolleway/commons-uploader.git
cd commons-uploader 

#run commands from termux-deploy.sh
```


## Usage

Upload files for building from directory 
```
./building-upload.py https://www.wikidata.org/wiki/Q118113014 i/3k2 --dry
```

Create building and upload files from directory i/21
```
./add-building.py --street "Волжский бульвар" --housenumber "21" --coords "55.70592 37.74983" -cs osm --levels 5 --levels_url https://www.reformagkh.ru/myhouse/profile/view/8113254 --year 1962 --year_url https://www.reformagkh.ru/myhouse/profile/view/8113254 --photos i/21 #г. Москва, б-р. Волжский, д. 21
```

## Used image params

* GPS coordinates
* DateTime
* GPS Dest coordinates optional
* Make optional
* Model optional
* Lens model optional
* F number optional
* focal length in 35mm format optional




