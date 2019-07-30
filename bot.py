#!/usr/bin/env python

from __future__ import print_function

import logging
from typing import List

from lang import Lang
from player import Player


class ChatBot:
    def __init__(self, players: List[Player], lang: Lang):
        self.__logger = logging.getLogger("Bot")
        self.__lang = lang
        logging.basicConfig(level=logging.INFO)
        self.__players = players

    def __find_player(self, username: str) -> Player:
        for player in self.__players:
            if player.username == username:
                return player
        raise PlayerNotFoundException(username, self.__lang.lang("bot.player.not_found").format(username=username))

    def command_respawn(self, args: List[str]):
        if len(args) == 0:
            self.__logger.info(self.__lang.lang("bot.player.respawn.all"))
            for player in self.__players:
                player.respawn()
        else:
            arg = args[0]
            try:
                player = self.__find_player(arg)
            except PlayerNotFoundException as e1:
                self.__logger.error(e1.message)
            else:
                self.__logger.info(self.__lang.lang("bot.player.respawn").format(username=arg))
                player.respawn()

    def command_chat(self, args: List[str]):
        if len(args) == 0:
            self.__logger.error(self.__lang.lang("bot.player.no_player"))
        else:
            if len(args) == 2:
                try:
                    player = self.__find_player(args[0])
                except PlayerNotFoundException as e1:
                    self.__logger.error(e1.message)
                else:
                    player.chat(args[1])

    def command_disconnect(self, args: List[str]):
        if len(args) == 0:
            for player in self.__players:
                player.disconnect()
        else:
            arg = args[0]
            try:
                player = self.__find_player(arg)
            except PlayerNotFoundException as e1:
                self.__logger.error(e1.message)
            else:
                player.disconnect()

    def command_reconnect(self, args: List[str]):
        if len(args) == 0:
            for player in self.__players:
                player.reconnect()
        else:
            arg = args[0]
            try:
                player = self.__find_player(arg)
            except PlayerNotFoundException as e1:
                self.__logger.error(e1.message)
            else:
                player.reconnect()

    def command_toggle_respawn(self, args: List[str]):
        if len(args) == 0:
            self.__logger.error(self.__lang.lang("bot.player.no_player"))
        else:
            try:
                player = self.__find_player(args[0])
            except PlayerNotFoundException as e1:
                self.__logger.error(e1.message)
            else:
                player.toggle_auto_respawn()

    def command_toggle_reconnect(self, args: List[str]):
        if len(args) == 0:
            self.__logger.error(self.__lang.lang("bot.player.no_player"))
        else:
            try:
                player = self.__find_player(args[0])
            except PlayerNotFoundException as e1:
                self.__logger.error(e1.message)
            else:
                player.toggle_auto_reconnect()

    def command_help(self, args: List[str]):
        self.__logger.info(self.__lang.lang("bot.player.command.list"))
        methods = [func for func in dir(self) if callable(getattr(self, func)) and func.startswith("command_")]
        for command in methods:
            self.__logger.info(command.replace("command_", "~"))

    # def command_connect(self, args: List[str]):
    #     if len(cmd) == 1:
    #             self.__logger.error("Please specify a player")
    #             continue
    #         if len(cmd) == 2:
    #             self.__logger.error("Please specify ip:port")
    #             continue
    #         # Try to split out port and address
    #         match = re.match(r"((?P<host>[^\[\]:]+)|\[(?P<addr>[^\[\]]+)\])"
    #                         r"(:(?P<port>\d+))?$", cmd[2])
    #         if match is None:
    #             raise ValueError("Invalid server address: '%s'." % cmd[2])
    #         address = match.group("host") or match.group("addr")
    #         port = int(match.group("port") or 25565)
    #         success_count = 0
    #         for player in self.__players:
    #             if player.username == cmd[1]:
    #                 player.connect(address,port)
    #                 success_count+=1
    #         if success_count == 0:
    #             self.__logger.error(
    #                 "Player {0} not found.".format(cmd[1]))

    def handle_text(self, text: str):
        if text.startswith("~"):
            raw = text.split(" ", 2)
            command = raw[0].lower()[1:]
            args = raw[1:]
            name = "command_{0}".format(command)
            try:
                method = getattr(self, name)
            except AttributeError:
                self.__logger.error(self.__lang.lang("bot.player.command.not_found").format(command=command))
            else:
                method(args)
        else:
            for player in self.__players:
                player.chat(text)

    def start_listening(self):
        while True:
            try:
                text = input("")
                self.handle_text(text)
            except KeyboardInterrupt:
                self.__logger.info(self.__lang.lang("bot.end"))
                exit()


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class PlayerNotFoundException(Error):

    def __init__(self, player, message):
        self.player = player
        self.message = message
