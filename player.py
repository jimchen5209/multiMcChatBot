#!/usr/bin/env python

from __future__ import print_function

import json
import logging
import threading

from minecraft.networking.connection import Connection
from minecraft.networking.packets import clientbound, serverbound
from minecraft.networking.types import AbsoluteHand

from lang import Lang


class Player:
    __retries = 0

    def __init__(self, username: str, connection: Connection, auto_reconnect: bool, auto_respawn: bool, lang: Lang):
        self.__auto_reconnect = auto_reconnect
        self.__auto_respawn = auto_respawn
        self.username = username
        self.__connection = connection
        self.__lang = lang

        self.__logger = logging.getLogger("Minecraft/{username}".format(username=self.username))
        logging.basicConfig(format="[%(asctime)s][%(levelname)s][%(name)s] %(message)s", level=logging.INFO)

        self.__connection.register_packet_listener(self.handle_join_game, clientbound.play.JoinGamePacket)
        self.__connection.register_packet_listener(self.print_chat, clientbound.play.ChatMessagePacket)
        self.__connection.register_packet_listener(self.handle_disconnect, clientbound.play.DisconnectPacket)
        self.__connection.register_packet_listener(self.handle_health_change, clientbound.play.UpdateHealthPacket)
        self.__connection.register_exception_handler(self.handle_exception)
        try:
            self.__connection.connect()
        except Exception as e:
            self.__logger.error(str(e))

    # def connect(self, ip, port):
    #     self.__init(self.username Connection)

    def reconnect(self):
        try:
            self.__connection.connect()
        except Exception as e:
            self.__logger.error(str(e))

    def handle_join_game(self, join_game_packet):
        self.__logger.info(self.__lang.lang("player.connected").format(
            server=self.__connection.options.address,
            port=self.__connection.options.port
        ))
        self.__retries = 0
        packet = serverbound.play.ClientSettingsPacket()
        packet.locale = self.__lang.lang_name
        packet.view_distance = 10
        packet.chat_mode = packet.ChatMode.FULL
        packet.chat_colors = False
        packet.displayed_skin_parts = packet.SkinParts.ALL
        packet.main_hand = AbsoluteHand.RIGHT
        self.__connection.write_packet(packet)

    def print_chat(self, chat_packet):
        self.__logger.info("[{position}] {message}".format(
            position=chat_packet.field_string('position'),
            message=self.__lang.parse_json(json.loads(chat_packet.json_data))
        ))

    def handle_disconnect(self, disconnect_packet):
        self.__logger.warning(
            self.__lang.lang("player.connection.lost").format(reason=(json.loads(disconnect_packet.json_data))))
        if self.__auto_reconnect:
            self.__retry()

    def handle_health_change(self, health_packet):
        self.__logger.warning(self.__lang.lang("player.health.changed").format(
            health=str(health_packet.health),
            food=str(health_packet.food),
            saturation=str(health_packet.food_saturation)))

        if self.__auto_respawn and health_packet.health == 0:
            self.__logger.info(self.__lang.lang("player.respawn.hint"))
            timer = threading.Timer(1.0, self.respawn)
            timer.start()

    def handle_exception(self, e, info):
        self.__logger.error("{type}: {message}".format(type=type(info[1]), message=str(e)))
        if self.__auto_reconnect:
            self.__retry()

    def __retry(self):
        self.__retries += 1
        if self.__retries >= 6:
            self.__retries = 0
            return
        self.__logger.info(self.__lang.lang("player.connection.retry").format(times=str(self.__retries)))
        timer = threading.Timer(5.0, self.reconnect)
        timer.start()

    def respawn(self):
        packet = serverbound.play.ClientStatusPacket()
        packet.action_id = serverbound.play.ClientStatusPacket.RESPAWN
        self.__connection.write_packet(packet)
        self.__logger.info(self.__lang.lang("player.respawned"))

    def disconnect(self):
        self.__connection.disconnect()
        self.__logger.info(self.__lang.lang("player.disconnected"))

    def toggle_auto_respawn(self):
        self.__auto_respawn = not self.__auto_respawn
        self.__logger.info(self.__lang.lang("player.auto_respawn.toggle").format(value=self.__auto_respawn))

    def toggle_auto_reconnect(self):
        self.__auto_reconnect = not self.__auto_reconnect
        self.__logger.info(self.__lang.lang("player.auto_reconnect.toggle").format(value=self.__auto_reconnect))

    def chat(self, text: str):
        if text == "":
            return
        packet = serverbound.play.ChatPacket()
        packet.message = text
        self.__connection.write_packet(packet)
