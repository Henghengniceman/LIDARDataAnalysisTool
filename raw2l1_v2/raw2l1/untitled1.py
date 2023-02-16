# -*- coding: utf-8 -*-
"""
Created on Fri Feb 25 19:50:41 2022

@author: ka1319
"""
from __future__ import print_function, division, absolute_import

import sys
from tools import lidar_reader as lr
from tools import arg_parser as ag
from tools import log
from tools import conf
from tools.check_conf import check_conf
from tools import create_netcdf as cnc
import pdb
import datetime
__author__ = 'Marc-Antoine Drouin'
__version__ = '2.1.17'


input_args = {'date': datetime.datetime(2018, 7, 12, 0, 0), 
                 'conf': 'C:\\DataAnalysisTool\\raw2l1_v2\\raw2l1\\conf\\conf_prod_KASCAL.ini',
                  'input': ['c:\\datos\\KASCAL\\0a\\2018\\07\\12\\RS_20180712_1216\\RM1871217.044746', 
                            'c:\\datos\\KASCAL\\0a\\2018\\07\\12\\RS_20180712_1216\\RM1871217.053891', 
                            'c:\\datos\\KASCAL\\0a\\2018\\07\\12\\RS_20180712_1216\\RM1871217.062837',
                            'c:\\datos\\KASCAL\\0a\\2018\\07\\12\\RS_20180712_1216\\RM1871217.071982', 
                            'c:\\datos\\KASCAL\\0a\\2018\\07\\12\\RS_20180712_1216\\RM1871217.462101'], 
                  'output': 'c:\\datos\\KASCAL\\1a\\2018\\07\\12\\kal_1a_Prs_rs_xf_2018071201.nc', 
                  'ancillary': [], 
                  'log': 'logs/raw2l1.log', 
                  'log_level': 'info', 
                  'verbose': 'info', 
                  'input_min_size': 0, 
                  'input_check_time': False, 
                  'input_max_age': datetime.timedelta(seconds=7200)}




# Read imput arguments
# -------------------------------------------------------------------------
# input_args = ag.get_input_args(argv)

# Start logger
# input_args['conf'].name = 'C:\\Lidar_Data\\raw2l1_v2\\raw2l1\\conf\\conf_prod_VELETA.ini'
# -------------------------------------------------------------------------
logger = log.init(input_args, 'raw2l1')
logger.info('logs are saved in {!s}'.format(input_args['log']))

# reading configuration file
# -------------------------------------------------------------------------
logger.debug('reading configuration file ' + input_args['conf'])
setting = conf.init(input_args, __version__, logger)
# pdb.set_trace()
logger.info('reading configuration file: OK')

# check configuration file
logger.debug('checking configuration file')
setting = check_conf(setting, logger)

# Add directory containing reader to path
# -------------------------------------------------------------------------
logger.debug("adding " + setting.get('conf', 'reader_dir') + " to path")
sys.path.append(setting.get('conf', 'reader_dir'))
# -------------------------------------------------------------------------
# pdb.set_trace()

logger.info("reading lidar data")
lidar_data = lr.RawDataReader(setting, logger)
lidar_data.read_data()
logger.info("reading data succeed")

aa1 = lidar_data.data

# checking read data if needed
# -------------------------------------------------------------------------
if input_args['input_check_time']:
    time_ok = lidar_data.timeliness_ok(input_args['input_max_age'], logger)
    if not time_ok:
        logger.critical("104 Data timeliness Error. Quitting raw2l1")
        sys.exit(1)

# pdb.set_trace()

# write netCDF file
# -------------------------------------------------------------------------
logger.info("writing output file")
cnc.create_netcdf(setting, lidar_data.data, logger)

# end of the program
# -------------------------------------------------------------------------
logger.info("end of processing")

# logger.info("reading lidar data")
# lidar_data = lr.RawDataReader(setting, logger)
# lidar_data.read_data()