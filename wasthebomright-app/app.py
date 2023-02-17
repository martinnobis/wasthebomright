import datetime
from ftplib import FTP
import json
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo
import urllib.parse

import boto3

import bom_scraper
import image_generator
import settings
import utils

DATA_BUCKET_NAME = "wasthebomright"


def bom_scraper_lambda(event, context):
    """Entry point for AWS Lambda.

    Creates a JSON file in S3 with the days observed temperatures and forecasts for all cities.
    """
    client = boto3.client("s3")
    todays_date = str(datetime.datetime.now(ZoneInfo("Australia/Melbourne")).date())

    data = bom_scraper.get_observations_and_future_forecasts_for_all_cities(todays_date)

    client.put_object(
        Body=bytes(json.dumps(data, indent=4).encode("UTF-8")),
        Bucket=DATA_BUCKET_NAME,  # TODO: should be renamed to something more descriptive
        Key=f"{todays_date}.json",
    )


def image_generator_lambda(event, context):
    """Entry point for AWS Lambda.

    Gets the previous days observation and forecast files and generates a plot image
    of the data.

    Should be triggered only when a new file is added to settings.BUCKET_NAME. It 
    doesn't actually have to retreive the last file added, but the last 7.
    """
    previous_days_data = utils.get_previous_days_data(settings.BUCKET_NAME)
    parsed_historical_data = utils.parse_historical_forecasts(previous_days_data)

    for (city, img) in image_generator.generate_images(parsed_historical_data):
        utils.upload_file(img, f"{utils.get_todays_date()}_{city}.png", settings.PLOT_BUCKET_NAME)
