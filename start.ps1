docker build --tag commons-uploader:1.0 .
docker run --rm -v "${PWD}:/opt/commons-uploader" -v "${PWD}/wikibase-cli:/root/.config/wikibase-cli" -v "${PWD}/wikibase-cache:/root/.cache/wikibase-cli" -it commons-uploader:1.0
