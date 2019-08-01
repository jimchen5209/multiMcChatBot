#!/usr/bin/env python

from __future__ import print_function

import logging
import os
import time
from copy import copy
from logging import Formatter

from colorama import init, Fore, Style, Back


class Logger:
    __logPath = "./logs/{0}".format(time.strftime("%Y-%m-%d-%H-%M-%S"))

    def __init__(self):
        init(autoreset=True)
        if not os.path.isdir("./logs"):
            os.mkdir("./logs")
        self.__log_format = "[%(asctime)s][%(threadName)s/%(name)s]%(levelname)s %(message)s"
        logging.root.name = "Main"
        logging.root.setLevel(logging.INFO)

        # color
        colored_formatter = ColoredFormatter(self.__log_format)
        stream = logging.StreamHandler()
        stream.setLevel(logging.INFO)
        stream.setFormatter(colored_formatter)

        self.logger = logging.getLogger()
        self.__handler = logging.FileHandler(
            filename="{0}.log".format(self.__logPath),
            encoding="utf-8",
            mode="w"
        )
        self.__handler.level = logging.INFO
        self.__handler.setFormatter(logging.Formatter(self.__log_format))
        self.logger.addHandler(self.__handler)
        self.logger.addHandler(stream)


class ColoredFormatter(Formatter):
    __mapping = {
        'DEBUG': Fore.LIGHTBLACK_EX,
        'INFO': Fore.WHITE,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.WHITE + Back.RED
    }

    def __init__(self, pattern):
        Formatter.__init__(self, pattern)

    def format(self, record):
        colored_record = copy(record)
        levelname = colored_record.levelname
        seq = self.__mapping.get(levelname, Fore.WHITE)
        colored_levelname = '%s[%s]%s' % (seq, levelname, Style.RESET_ALL)
        colored_record.levelname = colored_levelname
        return Formatter.format(self, colored_record)
