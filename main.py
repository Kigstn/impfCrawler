import json
import datetime
import time
import requests
import argparse

from logs import make_logger
from telegram import Telegram


def update_config(config: dict) -> dict:
    # telegram bot data
    if "bot_token" not in config:
        config["bot_token"] = input("Enter your telegram bot token")

    return config


def add_user(users: dict) -> dict:
    """ Info for every user who wants to get notified. zip code is the key for this dict to prevent too many requests"""

    # telegram data
    user_data = {"chat_id": input("Enter your telegram chat id")}

    zip_code = int(input("Enter your zip code"))
    try:
        users[zip_code].append(user_data)
    except KeyError:
        users[zip_code] = [user_data]

    return users


def currently_night(start: datetime.time, end: datetime.time, x: datetime.time):
    """Return true if x is in the range [start, end]"""

    if start <= end:
        return start <= x <= end
    else:
        return start <= x or x <= end


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--add_user', action='store_true', help='Add a new user')

    args = parser.parse_args()

    # create user file or get the existing one
    try:
        with open("users.json", 'r') as file:
            users = json.load(file)
    except FileNotFoundError:
        users = {}

    # create config file or get the existing one
    try:
        with open("config.json", 'r') as file:
            config = json.load(file)
    except FileNotFoundError:
        config = {}

    # if asked for, add a new user
    if args.add_user:
        # add new user
        users = add_user(users)

        # save new users
        with open("users.json", 'w+') as file:
            json.dump(users, file)

    # check if there are users
    assert users, "I found no users, please add some by using the argument --add_user"

    # check for missing entries
    config = update_config(config)

    # save new config
    with open("config.json", 'w+') as file:
        json.dump(config, file)

    # get logger
    logger = make_logger("main")

    # get telegram obj
    telegram = Telegram(config["bot_token"])

    # get data for the web requests
    headers = {
        'Accept': 'application/json'
    }

    # get night timeranges
    night_start = datetime.time(23, 0, 0)
    night_end = datetime.time(7, 0, 0)
    birth_date = int(datetime.datetime.strptime("01/01/00", "%d/%m/%y").timestamp() * 1e3)

    # loop and make a request every minute
    while True:
        now = datetime.datetime.now()

        # only check when it's day
        if currently_night(night_start, night_end, now.time()):
            time.sleep(2 * 60 * 60)
            continue

        for zip_code, zip_code_users in users.items():
            # zip code specific web request data
            url = f"https://www.impfportal-niedersachsen.de/portal/rest/appointments/findVaccinationCenterListFree/{zip_code}"

            params = {
                'birthdate': birth_date,
            }

            response = requests.get(url, params=params, headers=headers)
            response_json = response.json()

            # log that
            logger.debug(response)
            print(f"Checked at {str(now)}")

            # check if there is free spots
            if response.status_code == 200 and response_json:
                if response_json["resultList"]:
                    for centre in response_json["resultList"]:
                        if not centre["outOfStock"]:
                            # log that
                            logger.info(response_json)

                            # loop through the users
                            for user in zip_code_users:
                                # send the message via telegram
                                text = f"Es sind `{centre['freeSlotSizeOnline']}` Plätze im Impfzentrum `{centre['name']}` frei!\nGeimpft wird mit `{centre['vaccineName']}`\nDie ersten Termine sind ab `{str(datetime.datetime.fromtimestamp(centre['firstAppoinmentDateSorterOnline']/1e3))}`"
                                telegram.send(user["chat_id"], text)
                                print(text)

        # wait two minutes
        time.sleep(2*60)
