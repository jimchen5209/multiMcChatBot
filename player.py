#!/usr/bin/env python

from __future__ import print_function

import base64
import json
import logging
import threading

from minecraft import authentication
from minecraft.exceptions import LoginDisconnect, YggdrasilError
from minecraft.networking.connection import Connection
from minecraft.networking.packets import clientbound, serverbound
from minecraft.networking.types import AbsoluteHand

from lang import Lang


class Player:
    __retries = 0

    def __init__(self,
                 account: str,
                 password: str,
                 server_address: str,
                 port: int,
                 version: int,
                 auto_reconnect: bool,
                 auto_respawn: bool,
                 lang: Lang):
        self.__email = account
        self.__password = base64.b64encode(password.encode())
        self.__lang = lang

        self.__logger = logging.getLogger("Auth")
        logging.basicConfig(level=logging.INFO)

        tokens = self.__get_tokens()
        self.__auth = authentication.AuthenticationToken(
            username=self.__email,
            access_token=tokens["access"],
            client_token=tokens["client"]
        )
        self.auth()

        self.__auto_reconnect = auto_reconnect
        self.__auto_respawn = auto_respawn
        self.__connection = Connection(
            address=server_address,
            port=port,
            initial_version=version,
            auth_token=self.__auth
        )
        if not self.__auth.authenticated:
            return
        self.username = self.__auth.profile.name

        self.__logger = logging.getLogger(self.username)

        self.__connection.register_packet_listener(self.handle_join_game, clientbound.play.JoinGamePacket)
        self.__connection.register_packet_listener(self.print_chat, clientbound.play.ChatMessagePacket)
        self.__connection.register_packet_listener(self.handle_disconnect, clientbound.play.DisconnectPacket)
        self.__connection.register_packet_listener(self.handle_health_change, clientbound.play.UpdateHealthPacket)
        self.__connection.register_exception_handler(self.handle_exception)
        try:
            self.__connection.connect()
        except Exception as e:
            self.__logger.error(str(e))
            self.__retry()

    # def connect(self, ip, port):
    #     self.__init(self.username Connection)

    def __get_tokens(self) -> dict:
        try:
            with open('./data.json', 'r') as fs:
                auth = json.load(fs)
        except FileNotFoundError:
            return {
                "access": None,
                "client": None
            }
        else:
            if self.__email in auth:
                return auth[self.__email]
            else:
                return {
                    "access": None,
                    "client": None
                }

    def __refresh_tokens(self, access: str, client: str):
        auth = {}
        try:
            with open('./data.json', 'r') as fs:
                auth = json.load(fs)
        except FileNotFoundError:
            pass
        finally:
            auth[self.__email] = {
                "access": access,
                "client": client
            }
            with open('./data.json', 'w') as fs:
                json.dump(auth, fs, indent=2)

    def auth(self):
        try:
            self.__auth.refresh()
        except YggdrasilError:
            self.__login()
        except ValueError:
            self.__login()
        else:
            self.__logger.info(self.__lang.lang("main.auth.still_valid").format(email=self.__email))
            self.__refresh_tokens(access=self.__auth.access_token, client=self.__auth.client_token)

    def __login(self):
        self.__logger.info(self.__lang.lang("main.auth.login").format(email=self.__email))
        try:
            self.__auth.authenticate(
                username=self.__email,
                password=base64.b64decode(self.__password).decode()
            )
        except YggdrasilError as e:
            self.__logger.error(self.__lang.lang("main.auth.error").format(email=self.__email, message=str(e)))
        else:
            self.__refresh_tokens(access=self.__auth.access_token, client=self.__auth.client_token)

    def reconnect(self):
        try:
            self.__connection.connect()
        except Exception as e:
            self.__logger.error(str(e))
            self.__retry()

    # noinspection PyUnusedLocal
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
            self.__lang.lang("player.connection.lost").format(
                reason=self.__lang.parse_json(json.loads(disconnect_packet.json_data))))
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
        if type(info[1]) == LoginDisconnect:
            message = str(e).replace('The server rejected our login attempt with: "', '').replace('".', '')
            try:
                self.__logger.error(self.__lang.lang("player.connection.rejected").format(
                    reason=self.__lang.parse_json(json.loads(message))))
            except json.decoder.JSONDecodeError:
                self.__logger.error(self.__lang.lang("player.connection.rejected").format(reason=message))
        elif type(info[1]) == YggdrasilError:
            self.__logger.error(self.__lang.lang("player.session.expired"))
            self.auth()
            timer = threading.Timer(1.0, self.reconnect)
            timer.start()
            return
        else:
            self.__logger.error("{type}: {message}".format(type=type(info[1]), message=str(e)))
        if self.__auto_reconnect:
            if not self.__connection.connected:
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
