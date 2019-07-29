#!/usr/bin/env python

from __future__ import print_function

import json
import logging


class Config:
    def __init__(self, testing=False):
        self.__logger = logging.getLogger("Config")
        logging.basicConfig(format="[%(asctime)s][%(levelname)s][%(name)s] %(message)s", level=logging.INFO)
        self.__logger.info("Loading Config...")
        if testing:
            self.__logger.info("Testing mode detected, using testing config.")
            self.__configRaw = {
                "//accounts": "A list of accounts",
                "accounts": [{
                    "email": "",
                    "password": "",
                    "disabled": False
                }],
                "//server": "servers to connect to",
                "server": {
                    "ip": "localhost",
                    "port": 25565
                },
                "lang": "en_us",
                "auto_reconnect": True,
                "auto_respawn": True
            }
        else:
            try:
                with open('./config.json', 'r') as fs:
                    self.__configRaw = json.load(fs)
            except FileNotFoundError:
                self.__logger.error(
                    "Can't load config.json: File not found.")
                self.__logger.info("Generating empty config...")
                self.__configRaw = {
                    "//accounts": "A list of accounts",
                    "accounts": [{
                        "email": "",
                        "password": "",
                        "disabled": False
                    }],
                    "//server": "servers to connect to",
                    "server": {
                        "ip": "localhost",
                        "port": 25565
                    },
                    "lang": "en_us",
                    "auto_reconnect": True,
                    "auto_respawn": True
                }
                self.__save_config()
                self.__logger.error("Fill your config and try again.")
                exit()
            except json.decoder.JSONDecodeError as e1:
                self.__logger.error(
                    "Can't load config.json: JSON decode error:{0}".format(str(e1.args)))
                self.__logger.error("Check your config format and try again.")
                exit()
        self.accounts = self.__configRaw["accounts"]
        self.server = self.__configRaw["server"]
        self.lang = self.__configRaw["lang"]
        self.auto_reconnect = self.__configRaw["auto_reconnect"]
        self.auto_respawn = self.__configRaw["auto_respawn"]

    def __save_config(self):
        with open('./config.json', 'w') as fs:
            json.dump(self.__configRaw, fs, indent=2)
