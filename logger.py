#!/usr/bin/env python

from __future__ import print_function

import logging
import os
import time


class Logger:
    __logPath = "./logs/{0}".format(time.strftime("%Y-%m-%d-%H-%M-%S"))

    def __init__(self):
        if not os.path.isdir("./logs"):
            os.mkdir("./logs")
        self.__log_format = "[%(asctime)s][%(levelname)s][%(name)s] %(message)s"
        logging.root.name = "Minecraft"
        self.logger = logging.getLogger()
        logging.basicConfig(format=self.__log_format, level=logging.INFO)
        self.__handler = logging.FileHandler(
            filename="{0}.log".format(self.__logPath),
            encoding="utf-8",
            mode="w"
        )
        self.__handler.level = logging.INFO
        self.__handler.setFormatter(logging.Formatter(self.__log_format))
        self.logger.addHandler(self.__handler)
