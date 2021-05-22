import requests

from logs import make_logger


class Telegram:
    def __init__(self, chat_id: str, bot_token: str):
        self.chat_id = chat_id
        self.bot_token = bot_token

        self.headers = {
            'Accept': 'application/json',
        }

        # init logging
        self.logger = make_logger("telegram")

    # send a message
    def send(self, message):
        url = f'https://api.telegram.org/bot{self.bot_token}/sendMessage'
        params = {
            'chat_id': self.chat_id,
            'parse_mode': 'Markdown',
            'text': message
        }
        response = requests.get(url, params=params, headers=self.headers)

        # log that
        self.logger.debug(response)

        if response.status_code != 200:
            self.logger.info(response.json())
