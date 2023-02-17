#!/bin/sh

# build is a location specified also in template.yaml, so the `sam deploy` command
# knows where to look for the build.

rm -rf build/
python -m pip install -r requirements.txt -t build/
cp *.py build/

