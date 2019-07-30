#!/usr/bin/env python

from __future__ import print_function

import json
import logging
import os

from colorama import init, Fore, Style, Back


class Lang:
    __lang = {}

    def __init__(self, lang: str = "en_us"):
        init(autoreset=True)
        self.__color = Color()
        self.lang_name = lang
        self.__logger = logging.getLogger("Translation")
        logging.basicConfig(level=logging.INFO)
        self.__lang_load_list = ["lang/{lang}.json".format(lang=lang), "lang/minecraft/{lang}.json".format(lang=lang)]
        if not os.path.isdir("lang/custom"):
            os.mkdir("lang/custom")
        self.__find_lang("lang/custom")
        self.__logger.info("Loading languages: {0}".format(", ".join(self.__lang_load_list)))
        for lang_file in self.__lang_load_list:
            try:
                with open(lang_file, "r", encoding='utf8') as fs:
                    self.__lang.update(json.load(fs))
            except FileNotFoundError:
                self.__logger.warning("{lang} not found, some string may not work.".format(lang=lang_file))
            except json.decoder.JSONDecodeError as e:
                self.__logger.error(
                    "Error when loading {lang} and skipped, some string may not work.".format(lang=lang_file))
                self.__logger.error(str(e))
                continue

    def __find_lang(self, folder: str):
        for walk in os.walk(folder):
            for file in walk[2]:
                if file == "{lang}.json".format(lang=self.lang_name):
                    self.__lang_load_list.append(walk[0].replace('\\', '/') + "/" + file)

    def lang(self, lang_id: str) -> str:
        if lang_id in self.__lang:
            return self.__lang[lang_id]
        else:
            return lang_id

    def parse_json(self, json_data, flavor="console", default_style=""):
        if type(json_data) != dict:
            if flavor == "console":
                return default_style + self.__color.format_color(str(json_data))
            else:
                return str(json_data)
        text = ""
        style_prefix = ""
        style_suffix = ""  # todo other flavor
        if default_style == "":
            default_style = self.__color.DEFAULT
        if flavor == "console":
            if "color" in json_data:
                style_prefix += self.__color.get_color_from_string(json_data['color'].upper())
            else:
                style_prefix += default_style
            if "bold" in json_data:
                if json_data['bold']:
                    style_prefix += self.__color.BOLD
            if "italic" in json_data:
                if json_data['italic']:
                    style_prefix += self.__color.ITALIC
            if "underlined" in json_data:
                if json_data['underlined']:
                    style_prefix += self.__color.UNDERLINE
            if "strikethrough" in json_data:
                if json_data['strikethrough']:
                    style_prefix += self.__color.STRIKE_THROUGH
            style_suffix += self.__color.CONSOLE_RESET
        if "translate" in json_data:
            if json_data["translate"] in self.__lang:
                text = style_prefix + self.__lang[json_data["translate"]] + style_suffix
                if 'with' in json_data:
                    with_text = []
                    for i in json_data['with']:
                        with_text.append(style_suffix + self.parse_json(i, default_style=style_prefix) + style_prefix)
                    if "%1$s" in text:
                        tmp_num = 1
                        while True:
                            tmp_str = "%{0}$s".format(str(tmp_num))
                            tmp_str_to_replace = "{" + str(tmp_num - 1) + "}"
                            if tmp_str in text:
                                text = text.replace(tmp_str, tmp_str_to_replace)
                            else:
                                break
                            tmp_num += 1
                        text = text.format(*with_text)
                    while len(with_text) > text.count("%s"):
                        with_text.pop()
                    text = text % tuple(with_text)
            else:
                text = style_prefix + json_data["translate"] + style_suffix
        elif "text" in json_data:
            text = style_prefix + json_data["text"] + style_suffix
        elif "score" in json_data:
            text = style_prefix + json_data['score']['value'] + style_suffix
        if "extra" in json_data:
            for i in json_data["extra"]:
                text += self.parse_json(i, default_style=style_prefix)
        return text


class Color:
    BLACK = Fore.BLACK + Back.WHITE
    DARK_BLUE = Fore.BLUE
    DARK_GREEN = Fore.GREEN
    DARK_AQUA = Fore.CYAN
    DARK_RED = Fore.RED
    DARK_PURPLE = Fore.MAGENTA
    GOLD = Fore.YELLOW
    GRAY = Style.DIM + Fore.WHITE
    DARK_GRAY = Fore.LIGHTBLACK_EX
    BLUE = Fore.LIGHTBLUE_EX
    GREEN = Fore.LIGHTGREEN_EX
    AQUA = Fore.LIGHTCYAN_EX
    RED = Fore.LIGHTRED_EX
    LIGHT_PURPLE = Fore.LIGHTMAGENTA_EX
    YELLOW = Fore.LIGHTYELLOW_EX
    WHITE = Fore.LIGHTWHITE_EX
    BOLD = "\033[01m"
    ITALIC = "\033[07m"
    UNDERLINE = "\033[04m"
    STRIKE_THROUGH = "\033[09m"
    DEFAULT = WHITE
    RESET = Style.RESET_ALL + DEFAULT
    CONSOLE_RESET = Style.RESET_ALL
    __COLOR_CODES = {
        "§0": RESET + BLACK,
        "§1": RESET + DARK_BLUE,
        "§2": RESET + DARK_GREEN,
        "§3": RESET + DARK_AQUA,
        "§4": RESET + DARK_RED,
        "§5": RESET + DARK_PURPLE,
        "§6": RESET + GOLD,
        "§7": RESET + GRAY,
        "§8": RESET + DARK_GRAY,
        "§9": RESET + BLUE,
        "§A": RESET + GREEN,
        "§a": RESET + GREEN,
        "§B": RESET + AQUA,
        "§b": RESET + AQUA,
        "§C": RESET + RED,
        "§c": RESET + RED,
        "§D": RESET + LIGHT_PURPLE,
        "§d": RESET + LIGHT_PURPLE,
        "§E": RESET + YELLOW,
        "§e": RESET + YELLOW,
        "§F": RESET + WHITE,
        "§f": RESET + WHITE,
        "§L": BOLD,
        "§l": BOLD,
        "§M": STRIKE_THROUGH,
        "§m": STRIKE_THROUGH,
        "§N": UNDERLINE,
        "§n": UNDERLINE,
        "§O": ITALIC,
        "§o": ITALIC,
        "§R": RESET,
        "§r": RESET,
        "§K": "",
        "§k": ""
    }

    def format_color(self, text: str) -> str:
        tmp_text = text
        for color in self.__COLOR_CODES:
            tmp_text.replace(color, self.__COLOR_CODES[color])
        return tmp_text

    def get_color_from_string(self, color: str) -> str:
        return getattr(self, color)
