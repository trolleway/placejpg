docker build --tag placejpg:2023.11 .

docker run --rm -v "${PWD}:/opt/commons-uploader" -it placejpg:2023.11
