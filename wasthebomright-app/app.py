import json

import boto3

import bom_scraper
import image_generator
import settings
import utils

OBSERVATIONS_MIN_BUCKET_NAME = "observations-min"
OBSERVATIONS_MAX_BUCKET_NAME = "observations-max"
FORECASTS_BUCKET_NAME = "bom-forecasts"
PARSED_FORECASTS_BUCKET_NAME = "parsed-bom-forecasts"
IMAGES_BUCKET_NAME = "images"


def obs_min_lambda(event, context):
    """Entry point for AWS Lambda. """
    client = boto3.client("s3")

    data = bom_scraper.get_observations_data("min")

    client.put_object(
        Body=bytes(json.dumps(data, indent=4).encode("UTF-8")),
        Bucket=OBSERVATIONS_MIN_BUCKET_NAME,
        Key=f"min_obs_{utils.get_yesterdays_date()}.json",
    )

def obs_max_lambda(event, context):
    """Entry point for AWS Lambda."""
    client = boto3.client("s3")

    data = bom_scraper.get_observations_data("max")

    client.put_object(
        Body=bytes(json.dumps(data, indent=4).encode("UTF-8")),
        Bucket=OBSERVATIONS_MAX_BUCKET_NAME,
        Key=f"max_obs_{utils.get_todays_date()}.json",
    )


def forecasts_lambda(event, context):
    """Entry point for AWS Lambda."""
    client = boto3.client("s3")

    data = bom_scraper.get_forecasts_data()

    client.put_object(
        Body=bytes(json.dumps(data, indent=4).encode("UTF-8")),
        Bucket=OBSERVATIONS_MAX_BUCKET_NAME,
        Key=f"forecasts_{utils.get_todays_date()}.json",
    )



def parse_forecasts_lambda(event, context):
    """Entry point for AWS Lambda."""
    client = boto3.client("s3")

    # get the observation file (which is what triggered this lambda), the scheduled event
    # which triggers this function passes through an argument of the form:
    # { "type": "min" } or { "type": "max" }
    if event["type"] == "min":
        day = utils.get_yesterdays_date()
        forecasts = utils.get_previous_days_data(OBSERVATIONS_MIN_BUCKET_NAME)
        obs = utils.get_obj(client, OBSERVATIONS_MIN_BUCKET_NAME, f"obs_min_{day}.json")
    elif event["type"] == "max":
        day = utils.get_todays_date()
        forecasts = utils.get_previous_days_data(OBSERVATIONS_MAX_BUCKET_NAME, skip_latest=True)
        obs = utils.get_obj(client, OBSERVATIONS_MAX_BUCKET_NAME, f"obs_max_{day}.json")
    else:
        raise ValueError(f"Could not recognise event type argument: {event}")

    data = utils.parse_historical_forecasts(forecasts, obs, event["type"])

    client.put_object(
        Body=bytes(json.dumps(data, indent=4).encode("UTF-8")),
        Bucket=PARSED_FORECASTS_BUCKET_NAME,
        Key=f"parsed_{event['type']}_{day}.json",
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
