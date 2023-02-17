"""Parses observed temp measurements and generates legacy forecasts results.

** Plot is hardcoded to consider latest file to contain todays observation. **
So either run it late in the day, or give it yesterday's file as the latest.
"""
import argparse
from io import BytesIO
import json 
import glob

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import (AutoMinorLocator, MultipleLocator)

import settings
import utils


def plot(city):
    fig, ax = plt.subplots()  # Create a figure containing a single axes.

    x = [0, -1, -2, -3, -4, -5, -6]
    labels = ["yesterday", "2\ndays ago", "3\ndays ago", "4\ndays ago", "5\ndays ago", "6\ndays ago", "7\ndays ago"]

    ax.set_ylabel("Temperature (°C)")
    ax.set_xlabel("Forecasts")
    ax.set_xticks(x, labels)
    ax.plot(x, [city["todays_max"]] * 7, linestyle="dashed")
    ax.annotate('Today\'s max', xy=(-0.5, city["todays_max"] + .1))
    ax.plot(x, [city["todays_min"]] * 7, linestyle="dashed")
    ax.annotate('Today\'s min', xy=(-0.5, city["todays_min"] + .1))
    max_forecasts = []
    min_forecasts = []
    idx = 0
    for forecast in city["forecasts"]:
        max_forecasts.append(forecast["max"])
        plt.annotate(forecast["max"], (idx, forecast["max"]), textcoords="offset points", xytext=(0, -12), ha="center")

        min_forecasts.append(forecast["min"])
        plt.annotate(forecast["min"], (idx, forecast["min"]), textcoords="offset points", xytext=(0, 10), ha="center")
        idx = idx - 1

    ax.fill_between(x, max_forecasts, [city["todays_max"]] * 7, alpha=0.2)
    ax.fill_between(x, min_forecasts, [city["todays_min"]] * 7, color="C1", alpha=0.2)

    ax.plot([0, -1, -2, -3, -4, -5, -6], max_forecasts, marker="x")
    ax.plot([0, -1, -2, -3, -4, -5, -6], min_forecasts, marker="x")

    ax.set_title("Forecast vs actual")
    ax.yaxis.set_major_locator(MultipleLocator(1))
    ax.yaxis.set_minor_locator(AutoMinorLocator(2))
    # ax.grid(axis="y", which="minor", alpha=0.4, linestyle='--')
    ax.grid(axis="y", which="major", alpha=0.4, linestyle='--')

    # fig, ax = plt.subplots()  # Create a figure containing a single axes.
    # ax.plot([0, -1, -2, -3], [1, 4, 2, 3]);  # Plot some data on the axes.
    # ax.plot([1, 2, 3, 4], [2, 3, 1, 3]);  # Plot some data on the axes.
    # ax.plot([1, 2, 3, 4], [2, 2, 2, 2]);  # Plot some data on the axes.



def generate_images(data_file):
    """Generate an image and returns the binaries for each city in data_file.
    
    data_file contains for each city a list of observations and future forecasts.

    Returns a list of binary objects of each city's PNG file.
    """
    img_binaries = []
    for city in data_file:
        plt = plot(city)

        data_obj = BytesIO()
        plt.savefig(data_obj, format='png')
        img_binaries.append((city, data_obj))

    return img_binaries


def main():
    """Hardcoded to use the files in real_data/obs_and_forecast_files.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-c",
                        "--city",
                        action="store",
                        dest="city",
                        type=str,
                        help = "City to plot."
    )
    args = parser.parse_args()

    if args.city not in settings.CITIES:
        raise ValueError(f"City {args.city} not in {', '.join(settings.CITIES.keys())}. Choose an existing city.")

    obs_and_forecast_data = []
    for data_file in glob.glob("./real_data/obs_and_forecast_files/*"):
        with open(data_file) as f:
            obs_and_forecast_data.append(json.load(f))

    parsed_data = utils.parse_historical_forecasts(obs_and_forecast_data)

    # print(json.dumps(parsed_data, indent=4))
    # exit()

    for city_key in settings.CITIES.keys():
        if city_key == args.city:
            city_data = parsed_data["cities"][city_key]
            plot(city_data)

            plt.show()
    # plt.savefig("plot.png")


if __name__ == "__main__":
    main()
