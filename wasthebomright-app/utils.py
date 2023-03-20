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


def get_obj(client, bucket_name, obj_name):
    """Get object (file) from an S3 bucket."""
    obj = client.Object(bucket_name, obj_name)
    return obj.get()["Body"].read().decode("utf-8")


def get_previous_days_data(bucket_name, skip_latest=False):
    """Previous as in the last few days, not just yesterday.
    
    Returns a list of dicts from the bucket. Each dict is a separate loaded JSON file.
    
    Use skip_latest to not include the latest forecast. This is for the evening trigger at 9:30PM
    to ignore the forecast made a 3PM that same day as it wouldn't make sense to include a forecast
    made on the same day."""
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(bucket_name)

    object_names = bucket.objects.all()

    # names are dates so they can be sorted
    object_names = sorted(
        [s.key for s in object_names], reverse=True
    )  # sort in descending order to get today's into index 0

    selected_object_names = [
        object_names[0],
        object_names[1],
        object_names[2],
        object_names[3],
        object_names[4],
        object_names[5],
        object_names[6],
    ]

    if skip_latest:
        selected_object_names = selected_object_names[1:]
        selected_object_names += object_names[7]

    return [json.loads(get_obj(s3, bucket_name, o)) for o in selected_object_names]


def parse_historical_forecasts(forecasts: dict, obs: dict, type: str):
    """Takes the historical forecasts for the previous week and the observation for
    today and returns a friendlier format for use by the image generator.
    
    output: a nice dict containing todays observed temps and historical forecasts with the delta.
    
    Example obs file:
        {
            "MEL": 17.3,
            "ADL": 15.7,
            "SYD": 20.7,
            "BNE": 22.8,
            "PER": 16.6,
            "CAN": 10.2,
            "HOB": 11.6,
            "DAR": 23.4,
            "day": "2023-03-18"
        }

    Example forecasts file:
        {
            "accessed": "2023-03-20",
            "MEL": [
                {
                    "day": "2023-03-21T00:00:00+11:00",
                    "max": 21.0,
                    "min": 13.0
                },
                {
                    "day": "2023-03-22T00:00:00+11:00",
                    "max": 24.0,
                    "min": 16.0
                },
                {
                    "day": "2023-03-23T00:00:00+11:00",
                    "max": 24.0,
                    "min": 15.0
                },
                {
                    "day": "2023-03-24T00:00:00+11:00",
                    "max": 21.0,
                    "min": 16.0
                },
                {
                    "day": "2023-03-25T00:00:00+11:00",
                    "max": 21.0,
                    "min": 14.0
                },
                {
                    "day": "2023-03-26T00:00:00+11:00",
                    "max": 22.0,
                    "min": 13.0
                },
                {
                    "day": "2023-03-27T00:00:00+11:00",
                    "max": 22.0,
                    "min": 14.0
                }
            ],
            ... (other cities)
        }
    """
    obs_date = obs["day"]  # would be todays for a max obs, or yesterdays for a min obs

    parsed_historical_forecasts = { "day": str(obs_date) }

    for city in settings.CITIES.keys():
        todays_obs = float(obs[city])

        data = {"obs": todays_obs, "forecasts": []}

        # get the historical forecasts for today
        for f in forecasts[city]:
            if f["day"].startswith(str(obs_date)):
                if type == "min":
                    forecast_min = float(f["min"])
                    data["forecasts"].append(
                        {
                            "day": f["day"],
                            "forecast": forecast_min,
                            "diff": round(todays_obs - forecast_min, 2),
                        }
                    )
                else:
                    forecast_max = float(f["max"])
                    data["forecasts"].append(
                        {
                            "day": f["day"],
                            "forecast": forecast_max,
                            "diff": round(todays_obs - forecast_max, 2),
                        }
                    )

        parsed_historical_forecasts[city] = data

    return parsed_historical_forecasts 