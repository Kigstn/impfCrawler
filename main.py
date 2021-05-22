import json
import datetime
import time

import requests

from logs import make_logger
from telegram import Telegram


def update_config(config: dict) -> dict:
    # vaccination centre data
    if "zip_code" not in config:
        config["zip_code"] = int(input("Enter your zip code"))
    if "birth_date" not in config:
        birth_date = input("Enter your birth date like 'dd/mm/yy'")
        config["birth_date"] = int(datetime.datetime.strptime(birth_date, "%d/%m/%y").timestamp() * 1e3)

    # telegram bot data
    if "bot_token" not in config:
        config["bot_token"] = input("Enter your telegram bot token")
    if "chat_id" not in config:
        config["chat_id"] = input("Enter your telegram chat id")

    return config


def currently_night(start: datetime.time, end: datetime.time, x: datetime.time):
    """Return true if x is in the range [start, end]"""

    if start <= end:
        return start <= x <= end
    else:
        return start <= x or x <= end


if __name__ == '__main__':
    # create config file or get the existing one
    try:
        with open("config.json", 'r') as file:
            config = json.load(file)
    except FileNotFoundError:
        config = {}

    # check for missing entries
    config = update_config(config)

    # save new config
    with open("config.json", 'w+') as file:
        json.dump(config, file)

    # get logger
    logger = make_logger("main")

    # get telegram obj
    telegram = Telegram(config["chat_id"], config["bot_token"])

    # get data for the web requests
    url = f"https://www.impfportal-niedersachsen.de/portal/rest/appointments/findVaccinationCenterListFree/{config['zip_code']}"
    headers = {
        'Accept': 'application/json'
    }
    params = {
        'birthdate': config["birth_date"],
    }

    # get night timeranges
    night_start = datetime.time(23, 0, 0)
    night_end = datetime.time(7, 0, 0)

    # loop and make a request every minute
    while True:
        response = requests.get(url, params=params, headers=headers)
        response_json = response.json()

        # log that
        logger.debug(response)
        now = datetime.datetime.now()
        print(f"Checked at {str(now)}")

        # check if there is free spots
        if response.status_code == 200 and response_json:
            if response_json["resultList"]:
                found_one = False
                for centre in response_json["resultList"]:
                    if not centre["outOfStock"]:
                        # log that
                        logger.info(response_json)

                        # send the message via telegram
                        text = f"Es sind `{centre['freeSlotSizeOnline']}` Plätze im Impfzentrum `{centre['name']}` frei!\nGeimpft wird mit `{centre['vaccineName']}`\nDie ersten Termine sind ab `{str(datetime.datetime.fromtimestamp(centre['firstAppoinmentDateSorterOnline']/1e3))}`"
                        telegram.send(text)
                        print(text)
                        found_one = True

                # if it's the middle of the night, wait 2 hours to not spam
                if found_one and currently_night(night_start, night_end, now.time()):
                    time.sleep(2*60*60)

        # wait two minutes
        time.sleep(2*60)
