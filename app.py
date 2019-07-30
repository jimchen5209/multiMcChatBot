#!/usr/bin/env python

from __future__ import print_function

import time

from bot import ChatBot
from config import Config
from lang import Lang
from logger import Logger
from player import Player


def main():
    config = Config()
    logger = Logger()
    lang = Lang(config.lang)
    players = []

    for account in config.accounts:
        if account["disabled"]:
            logger.logger.info(lang.lang("main.auth.disabled").format(email=account["email"]))
            continue
        player = Player(
            account=account["email"],
            password=account["password"],
            server_address=config.server["ip"],
            port=config.server["port"],
            version=498,
            auto_reconnect=config.auto_reconnect,
            auto_respawn=config.auto_respawn,
            lang=lang
        )
        players.append(player)
        time.sleep(1)

    bot = ChatBot(players, lang)
    bot.start_listening()


if __name__ == "__main__":
    main()
