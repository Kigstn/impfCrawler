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

    # loop and make a request every minute
    while True:
        response = requests.get(url, params=params, headers=headers)
        response_json = response.json()

        # log that
        logger.debug(response)
        print(f"Checked at {str(datetime.datetime.now())}")

        # check if there is free spots
        if response.status_code == 200 and response_json:
            if response_json["resultList"]:
                found_one = False
                for centre in response_json["resultList"]:
                    if not centre["outOfStock"]:
                        text = f"Es sind Plätze im Impfzentrum `{centre['name']}` frei!\nGeimpft wird mit `{centre['vaccineName']}`"
                        telegram.send(text)
                        found_one = True

                        # log that
                        logger.info(response_json)
                        print(text)

                # wait 4 hours to not spam
                if found_one:
                    time.sleep(4*60*60)

        # wait two minutes
        time.sleep(2*60)
