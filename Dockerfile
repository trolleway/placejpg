FROM ubuntu:22.04
ARG DEBIAN_FRONTEND=noninteractive
ARG APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=DontWarn

RUN apt-get update 
RUN apt-get install --no-install-recommends --fix-missing -y \
    jq python3-pip nodejs npm gdal-bin proj-data libxml2-utils nano
	
	


RUN npm install -g wikibase-cli

RUN apt-get install -y libimage-exiftool-perl


RUN mkdir /opt/commons-uploader

RUN chmod  --recursive 777 /opt/commons-uploader

WORKDIR /opt/commons-uploader
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

RUN wb config instance https://www.wikidata.org
RUN wb config sparql-endpoint https://query.wikidata.org/sparql


CMD ["/bin/bash"]
