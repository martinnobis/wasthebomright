"""Get observed temp measurements and future forecast data from the BOM."""
import datetime
from ftplib import FTP
import io
import json
import logging
import os
import sys
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

import settings
import utils 


log_Format = "%(levelname)s %(asctime)s - %(message)s"
logging.basicConfig(stream=sys.stdout, format=log_Format, level=logging.INFO)
logger = logging.getLogger()


# def get_ftp_file(filename):
#     write_file = os.path.join(settings.DOWNLOAD_DIR, filename)

#     if os.path.isfile(write_file):
#         logger.warning(f"File '{filename}' already downloaded.")
#     else:
#         with FTP("ftp.bom.gov.au") as ftp:
#             ftp.login()
#             ftp.cwd("anon/gen/fwo/")

#             if not os.path.exists(settings.DOWNLOAD_DIR):
#                 os.makedirs(settings.DOWNLOAD_DIR)

#             logger.info(f"Downloading '{filename}' to '{write_file}.")

#             with open(write_file, "wb") as fp:
#                 ftp.retrbinary(f"RETR {filename}", fp.write)

#     return write_file


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


def get_observation(city):
    """Get today's max & min temperatures."""
    try:
        remote_filename = settings.CITIES[city]["observation_file"]
        station = settings.CITIES[city]["station"]
    except KeyError:
        raise ValueError(f"Coud not find city {city}.")

    xml_str = get_ftp_str(remote_filename)

    root = ET.ElementTree(ET.fromstring(xml_str))

    # day_query = ".//station[@stn-name='{station}']//period"
    max_query = (
        ".//station[@stn-name='{station}']//element[@type='maximum_air_temperature']"
    )
    min_query = (
        ".//station[@stn-name='{station}']//element[@type='minimum_air_temperature']"
    )

    max = root.find(max_query.format(station=station)).text
    min = root.find(min_query.format(station=station)).text

    return {"max": float(max), "min": float(min)}


def get_future_forecasts(city):
    """Get today's future forecasts (for the next week)."""
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


def get_observations_and_future_forecasts_for_all_cities(todays_date):
    """Get observerations and future forecasts for all cities defined in settings."""
    data = {"day": todays_date, "cities": {}}

    for city in settings.CITIES.keys():
        data["cities"][city] = {
            "observation": get_observation(city),
            "forecasts": get_future_forecasts(city),
        }

    return data


def main():
    """Entry point for local testing.

    Output file is put into settings.LOCAL_OUTPUT_DIR.
    """
    todays_date = utils.get_todays_date()

    if not os.path.exists(settings.LOCAL_OUTPUT_DIR):
        os.makedirs(settings.LOCAL_OUTPUT_DIR)

    output_file = os.path.join(settings.LOCAL_OUTPUT_DIR, f"observation_and_forecast_{todays_date}.json")

    out_file = json.dumps(get_observations_and_future_forecasts_for_all_cities(todays_date), indent=4)

    with open(output_file, "w") as f:
        f.write(out_file)


if __name__ == "__main__":
    main()
