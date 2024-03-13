#!/usr/bin/env python3

# Copyright (C) 2021-2022, Xilinx, Inc.  All rights reserved.
# Copyright (C) 2022, Advanced Micro Devices, Inc.  All rights reserved.
#
# Author:
#       Raju Kumar Pothuraju <rajukumar.pothuraju>
#
# SPDX-License-Identifier: MIT

import logging
import sys

logger = None
format = logging.Formatter("[%(levelname)s] %(message)s")


def plain(self, message, *args, **kwargs):
    print(message)


def note(self, message, *args, **kwargs):
    self._log(logging.INFO + 2, message, args, **kwargs)


logging.addLevelName(logging.INFO + 2, 'NOTE')
logging.Logger.plain = plain
logging.Logger.note = note


def setup_logger(name):
    global logger
    if logger:
        return logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    console_h = logging.StreamHandler(sys.stdout)
    console_h.setLevel(logging.INFO)
    console_h.setFormatter(format)
    logger.addHandler(console_h)

    return logger, console_h


def setup_logger_file(filename):
    global logger
    file_h = logging.FileHandler(filename)
    file_h.setLevel(logging.DEBUG)
    file_h.setFormatter(format)
    logger.addHandler(file_h)
