"""Get observed temp measurements and future forecast data from the BOM."""
from ftplib import FTP
import io
import json
import logging
import os
import sys
import xml.etree.ElementTree as ET

import settings
import utils 


log_Format = "%(levelname)s %(asctime)s - %(message)s"
logging.basicConfig(stream=sys.stdout, format=log_Format, level=logging.INFO)
logger = logging.getLogger()


def get_ftp_str(filename):
    """Get BOM XML data as string."""
    with FTP("ftp.bom.gov.au") as ftp:
        ftp.login()
        ftp.cwd("anon/gen/fwo/")

        logger.info(f"Downloading '{filename}'.")

        with io.StringIO() as buffer_io:
            ftp.retrlines(f"RETR {filename}", buffer_io.write)
            content = buffer_io.getvalue()

    return content


def get_observation(city, type):
    """Get today's max or min observed temperature.
    
    TODO: clarify the time period.
    """
    if type not in ("min", "max"):
        raise ValueError(f"type argument must be either 'min' or 'max', not {type}.")

    try:
        remote_filename = settings.CITIES[city]["observation_file"]
        station = settings.CITIES[city]["station"]
    except KeyError:
        raise ValueError(f"Coud not find city {city}.")

    xml_str = get_ftp_str(remote_filename)

    root = ET.ElementTree(ET.fromstring(xml_str))

    # day_query = ".//station[@stn-name='{station}']//period"

    query = f".//station[@stn-name='{station}']//element[@type='{type}imum_air_temperature']"

    obs = root.find(query).text
    return float(obs)


def get_future_forecasts(city):
    """Get today's future forecasts (for the next 6 days)."""
    try:
        remote_filename = settings.CITIES[city]["forecast_file"]
        area = settings.CITIES[city]["forecast_area"]
    except KeyError:
        raise ValueError(f"Coud not find city {city}.")

    xml_str = get_ftp_str(remote_filename)

    root = ET.ElementTree(ET.fromstring(xml_str))

    forecast_query = ".//area[@description='{area}']//forecast-period"

    nodes = root.findall(forecast_query.format(area=area))[
        1:
    ]  # ignore today's remaining forecast

    forecasts = []
    for node in nodes:
        day = node.get(
            "start-time-local"
        )  # date_object = datetime.strptime(day, '%Y-%m-%dT%H:%M:%S%z')
        max = node.find(".//element[@type='air_temperature_maximum']").text
        min = node.find(".//element[@type='air_temperature_minimum']").text
        forecasts.append({"day": day, "max": float(max), "min": float(min)})

    return forecasts


def get_observations_data(type: str) -> dict:
    """Returns obs data for all cities, ready to write to a file."""
    if type not in ("min", "max"):
        raise ValueError(f"type argument must be either 'min' or 'max', not {type}.")

    data = {}
    for city in settings.CITIES:
        data[city] = get_observation(city, type)

    if type == "min":
        data["day"] = utils.get_yesterdays_date()
    else:
        data["day"] = utils.get_todays_date()

    return data


def get_forecasts_data():
    """Returns forecast data for all cities, ready to write to a file."""
    data = {
        "accessed": utils.get_todays_date()
    }
    for city in settings.CITIES:
        data[city] = get_future_forecasts(city)
    
    return data


def get_observations_and_future_forecasts_for_all_cities(todays_date):
    """DEPRECATED. Replaced by the 3 functions above.
    
    Get observerations and future forecasts for all cities defined in settings.
    """
    data = {"day": todays_date, "cities": {}}

    for city in settings.CITIES.keys():
        data["cities"][city] = {
            "observation": get_observation(city),
            "forecasts": get_future_forecasts(city),
        }

    return data


def main():
    """Entry point for local testing.

    Output files are put into settings.LOCAL_OUTPUT_DIR.
    """
    if not os.path.exists(settings.LOCAL_OUTPUT_DIR):
        os.makedirs(settings.LOCAL_OUTPUT_DIR)

    # min observations
    data = get_observations_data("min")
    output_file = os.path.join(settings.LOCAL_OUTPUT_DIR, f"min_obs_{utils.get_yesterdays_date()}.json")

    with open(output_file, "w") as f:
        f.write(json.dumps(data, indent=4))

    # max observations
    data = get_observations_data("max")
    output_file = os.path.join(settings.LOCAL_OUTPUT_DIR, f"max_obs_{utils.get_todays_date()}.json")

    with open(output_file, "w") as f:
        f.write(json.dumps(data, indent=4))

    # forecasts
    data = get_forecasts_data()
    output_file = os.path.join(settings.LOCAL_OUTPUT_DIR, f"forecasts_{utils.get_todays_date()}.json")

    with open(output_file, "w") as f:
        f.write(json.dumps(data, indent=4))


if __name__ == "__main__":
    main()
