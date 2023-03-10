#!/bin/sh
# ~~Deprecated since using Docker~~

# build is a location specified also in template.yaml, so the `sam deploy` command
# knows where to look for the build.

rm -rf build/
python -m pip install -r requirements.txt -t build/
#cp app.py bom_scraper.py utils.py settings.py build/
cp *.py build/

