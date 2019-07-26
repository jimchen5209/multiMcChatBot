#!/usr/bin/env python

from __future__ import print_function

import json
import logging
import os


class Lang:
    __lang = {}

    def __init__(self, lang: str = "en_us"):
        self.lang_name = lang
        self.__logger = logging.getLogger("Translation")
        logging.basicConfig(format="[%(asctime)s][%(levelname)s][%(name)s] %(message)s", level=logging.INFO)
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

    def parse_json(self, json_data):
        if type(json_data) != dict:
            return str(json_data)
        text = ""
        if "translate" in json_data:
            if json_data["translate"] in self.__lang:
                text = self.__lang[json_data["translate"]]
                if 'with' in json_data:
                    with_text = []
                    for i in json_data['with']:
                        with_text.append(self.parse_json(i))
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
                text = json_data["translate"]
        elif "text" in json_data:
            text = json_data["text"]
        elif "score" in json_data:
            text = json_data['score']['value']
        if "extra" in json_data:
            for i in json_data["extra"]:
                text += self.parse_json(i)
        return text
