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
docker build
```

Run
```
docker run

# emulate upload files for building https://www.wikidata.org/wiki/Q118113014 witch has wikimedia commons category from directiry i
./building-upload.py https://www.wikidata.org/wiki/Q118113014 i --dry
```

### Install in Android / termux

```
pkg install git
git clone --depth 1 https://github.com/trolleway/commons-uploader.git
cd commons-uploader 

#run commands from termux-deploy.sh
```


## Usage

