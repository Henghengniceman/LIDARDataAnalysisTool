#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Compatibility with python 3
from __future__ import print_function, division, absolute_import

import logging
import logging.config
import os
import sys
from tools import utils
import pdb

LOG_FMT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FMT = '%Y-%m-%d %H:%M:%S'
LOG_DIR = 'logs'
LOG_FILENAME = 'raw2l1.log'


def init(opt, name):
    """
    Configure the logger and start it
    """

    # Check the logs directory
    log_dir = os.path.dirname(os.path.abspath(opt['log']))
    log_file = os.path.basename(opt['log'])
    #print('--------')
    #print(opt['log'])
    #print('log_dir: %s'%log_dir)
    #print('log_file: %s' % log_file)
    #print('--------')
    try:
        os.makedirs(log_dir)
    except Exception as e:
        print("%s already exists. no need to create" % log_dir)
    dir_ok = utils.check_dir(log_dir)
    if not dir_ok:
        print("critical - " + log_dir + " doesn't exist or is not writable")
        print("quitting raw2l1")
        sys.exit(1)

    filename = os.path.join(log_dir, log_file)
    print('debug file : {}'.format(filename))
    print('console debug level : {}'.format(opt['verbose'].upper()))
    print('file debug level : {}'.format(opt['log_level'].upper()))

    log_dict = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {
                "datefmt": LOG_DATE_FMT,
                "format": LOG_FMT,
            }
        },

        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": opt['verbose'].upper(),
                "formatter": "simple",
                "stream": "ext://sys.stdout"
            },
            "file_handler": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": opt['log_level'].upper(),
                "formatter": "simple",
                "filename": filename,
                "maxBytes": 10485760,
                "backupCount": 10,
                "encoding": "utf8"
            }
        },

        "root": {
            "level": 'DEBUG',
            "handlers": ["console", "file_handler"]
        }
    }

    logger = logging.getLogger(name)
    logging.config.dictConfig(log_dict)

    return logger
