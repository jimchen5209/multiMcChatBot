#!/usr/bin/env python

from __future__ import print_function

import json
import time

from minecraft import authentication
from minecraft.exceptions import YggdrasilError
from minecraft.networking.connection import Connection

from bot import ChatBot
from config import Config
from lang import Lang
from logger import Logger
from player import Player


def main():
    config = Config()
    logger = Logger()
    lang = Lang(config.lang)
    auth = {}
    auth_class = []
    players = []

    try:
        with open('./data.json', 'r') as fs:
            auth = json.load(fs)
    except FileNotFoundError:
        pass
    # auth
    for account in config.accounts:
        if account["email"] in auth:
            temp_auth = authentication.AuthenticationToken(
                username=account["email"],
                access_token=auth[account["email"]]['access'],
                client_token=auth[account["email"]]['client']
            )
            try:
                temp_auth.refresh()
            except YggdrasilError:
                logger.logger.info(lang.lang("main.auth.login").format(email=account["email"]))
                try:
                    temp_auth.authenticate(account["email"], account["password"])
                except YggdrasilError as e:
                    logger.logger.error(lang.lang("main.auth.error").format(email=account["email"], message=str(e)))
                    continue
                else:
                    auth[account["email"]] = {
                        "access": temp_auth.access_token,
                        "client": temp_auth.client_token
                    }
            else:
                logger.logger.info(lang.lang("main.auth.still_valid").format(email=account["email"]))
            auth_class.append(temp_auth)
        else:
            temp_auth = authentication.AuthenticationToken()
            logger.logger.info(lang.lang("main.auth.login").format(email=account["email"]))
            try:
                temp_auth.authenticate(
                    account["email"], account["password"])
            except YggdrasilError as e:
                logger.logger.error(
                    lang.lang("main.auth.error").format(email=account["email"], message=str(e)))
                continue
            else:
                auth[account["email"]] = {
                    "access": temp_auth.access_token,
                    "client": temp_auth.client_token
                }
            auth_class.append(temp_auth)
        time.sleep(1)

    with open('./data.json', 'w') as fs:
        json.dump(auth, fs, indent=2)

    for auth_data in auth_class:
        connection = Connection(
            config.server["ip"],
            config.server["port"],
            initial_version=498,
            auth_token=auth_data
        )
        player = Player(auth_data.profile.name, connection, config.auto_reconnect, config.auto_respawn, lang)
        players.append(player)
        time.sleep(1)

    bot = ChatBot(players, lang)
    bot.start_listening()


if __name__ == "__main__":
    main()
