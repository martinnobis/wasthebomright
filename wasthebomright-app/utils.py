"""Helper functions for accessing AWS S3 data."""
import datetime
import json
from zoneinfo import ZoneInfo

import boto3

import settings


def get_time() -> str:
    """Returns the time in Mel as '20:46:13'."""
    t = datetime.datetime.now(ZoneInfo("Australia/Melbourne")).time()
    return str(t)[:-7]  # strip off microseconds


def get_todays_date() -> str:
    """Returns today's date as '2023-02-12'."""
    d = datetime.datetime.now(ZoneInfo("Australia/Melbourne")).date()
    return str(d)


def get_yesterdays_date() -> str:
    """Returns yesterday's date as '2023-02-11'."""
    d = (datetime.datetime.now(ZoneInfo("Australia/Melbourne")) - datetime.timedelta(1)).date() 
    return str(d)


def upload_file(file, file_name, bucket):
    """Upload a file to an s3 bucket."""
    s3 = boto3.resource("s3")
    s3.upload_fileobj(file, bucket, file_name)


def get_obj(client, bucket_name, key):
    """Get object (file) from an S3 bucket."""
    obj = client.Object(bucket_name, key)
    return obj.get()["Body"].read().decode("utf-8")


def get_previous_days_data(bucket_name):
    """Previous as in the last few days, not just yesterday.
    
    Returns a list of dicts from the bucket. Each dict is a separate loaded JSON file."""
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(bucket_name)

    object_names = bucket.objects.all()

    # names are dates so they can be sorted
    object_names = sorted(
        [s.key for s in object_names], reverse=True
    )  # sort in descending order to get today's into index 0

    selected_object_names = [
        object_names[0],  # today's (TODO: doesn't work at all if this is yesterday's, fix this potential race condition)
        object_names[1],  # yesterday's
        object_names[2],  # 2 days ago
        object_names[3],  # 3 days ago
        object_names[4],  # 4 days ago
        object_names[5],  # 5 days ago
        object_names[6],  # 6 days ago
        object_names[7],  # 7 days ago
    ]

    return [json.loads(get_obj(s3, bucket_name, o)) for o in selected_object_names]


def parse_historical_forecasts(previous_days_data):
    """Takes the historical forecasts for the previous week and the observation for
    today and returns a friendlier format for use by the image generator.
    
    input: list of the last 7 day's forecasts for today, each item is a dict.
    output: a nice dict containing todays observed temps and historical forecasts with the delta.
    """
    todays_date = datetime.datetime.now().date()

    # get latest day's date
    previous_days_data = sorted(previous_days_data, key=lambda x: x["day"], reverse=True)  # sort in descending order to get today's into index 0
    todays_date = previous_days_data[0]["day"]

    parsed_historical_forecasts = {"date": str(todays_date), "cities": {}}

    for city in settings.CITIES.keys():
        # get today's observations, recall first item is today's
        todays_min = float(previous_days_data[0]["cities"][city]["observation"]["min"])
        todays_max = float(previous_days_data[0]["cities"][city]["observation"]["max"])

        data = {"todays_max": todays_max, "todays_min": todays_min, "forecasts": []}

        # get the historical forecasts for today
        for day in previous_days_data:
            for f in day["cities"][city]["forecasts"]:
                if f["day"].startswith(str(todays_date)):
                    forecast_min = float(f["min"])
                    forecast_max = float(f["max"])
                    data["forecasts"].append(
                        {
                            "day": day["day"],
                            "min": forecast_min,
                            "min_diff": round(todays_min - forecast_min, 2),
                            "max": forecast_max,
                            "max_diff": round(todays_max - forecast_max, 2),
                        }
                    )

        parsed_historical_forecasts["cities"][city] = data

    return parsed_historical_forecasts 