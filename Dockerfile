FROM ubuntu:latest
ARG DEBIAN_FRONTEND=noninteractive
ARG APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=DontWarn

RUN apt-get update && apt-get install --no-install-recommends --fix-missing -y \
    jq python3-pip  gdal-bin proj-data libxml2-utils nano
	
	




RUN apt-get install -y libimage-exiftool-perl
RUN apt-get install -y ffmpeg
RUN apt-get install -y git

RUN mkdir /opt/commons-uploader

RUN chmod  --recursive 777 /opt/commons-uploader

WORKDIR /opt/commons-uploader
COPY requirements.txt requirements.txt
#RUN pip3 uninstall --break-system-packages  setuptools
#RUN pip3 install --break-system-packages setuptools
RUN pip3 install  --break-system-packages -r requirements.txt 


CMD ["/bin/bash"]
