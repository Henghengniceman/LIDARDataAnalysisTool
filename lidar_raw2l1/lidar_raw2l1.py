import os, sys, glob
import shutil
import subprocess
import yaml
import argparse
import logging
import pdb

import datetime as dt
import numpy as np
import pandas as pd
import xarray as xr
from datetime import datetime,timedelta

# Source Code Dir
MODULE_DN = os.path.dirname(sys.modules[__name__].__file__)

""" logging  """
log_formatter = logging.Formatter('%(levelname)s: %(funcName)s(). L%(lineno)s: %(message)s')
logger = logging.getLogger(__name__)
if (logger.hasHandlers()):
    logger.handlers.clear()
handler = logging.StreamHandler(sys.stdout)
#    log_fn = os.path.join(RUN_DN, "raw2l1_%s.log" % dt.datetime.utcnow().strftime("%Y%m%dT%H%M"))
#        handler = logging.FileHandler(log_fn)
handler.setFormatter(log_formatter)
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.propagate = False


""" MEASUREMENT TYPES
"""
MEASUREMENT_TYPES_DAYLIKE = ['RS', 'OT', 'HF','FP']
MEASUREMENT_TYPES_FOLDERLIKE = ['DC', 'TC', 'DP']
MEASUREMENT_TYPES_FOLDERLIKE.extend(['TC-uv', 'TC-vnir', 'DP-pol', 'DP-rot'])
MEASUREMENT_TYPES_Scan = ['ZS', 'AS']
MEASUREMENT_TYPES = MEASUREMENT_TYPES_DAYLIKE + MEASUREMENT_TYPES_FOLDERLIKE + MEASUREMENT_TYPES_Scan 
MEASUREMENT_SUBTYPES = {
        'TC': ['N', 'E', 'S', 'W', 'N2'],
        'TC-uv': ['N', 'E', 'S', 'W', 'N2'],
        'TC-vnir': ['N', 'E', 'S', 'W', 'N2'],
        'DP': ['P45', 'N45'],
        'DP-rot': ['P45', 'N45'],
        'DP-pol': ['P45', 'N45']
        }

""" LIDAR INFO
"""
#TODO: incluir procesado de sd en alhambra cuando sepamos sus factores de conversion a magnitudes fisicas
LIDAR_NAMES = ['VELETA', 'MULHACEN', 'ALHAMBRA','KASCAL']
LIDAR_INFO = {
    'MULHACEN':{
        'nick': 'mhc',
        'conf_labels': ['rs_xf']
    },
    'VELETA':{
        'nick': 'vlt',
        'conf_labels': ['rs_xf']
    },
    'KASCAL':{
        'nick': 'kal',
        'conf_labels': ['rs_xf']
    },
    'ALHAMBRA':{
        'nick': 'alh',
        'conf_labels': ['rs_ff', 'rs_nf']
        #'conf_labels': ['pd', 'rs_ff', 'rs_nf', 'sd_ff', 'sd_nf']
    }
}

""" Functions """
def check_dir(dir_name):
    """
    Check if a directory exists and is writable
    """
    return os.access(dir_name, os.W_OK)


def check_measurement_type(meas_type):
    """
    Check Measurement Type
    """

    if meas_type not in MEASUREMENT_TYPES:
        logger.error("%s not a measurement type. Exit" % meas_type)
        sys.exit()
    #return True if meas_type in meas_types else False


def read_config(config_fn):
    """
    Read Configuration File for lidar_raw2l1
    If none is given, default config is read

    """

    config = {}
    if config_fn is None:
        config_fn = os.path.join(os.path.abspath(MODULE_DN), "config", "config_default.yaml")

    if os.path.isfile(config_fn):
        with open(config_fn) as f:
            config = yaml.full_load(f)
    else:
        logger.error("File %s does not exist. Exit" % config_fn)
        sys.exit()

    return config


def setup_lidar(lidar_name, data_dn, lidar_config_prod_fn=None, lidar_raw_iletter=None, lidar_config_dn=None):
    """ Setup of Lidar Information

    Args:
        lidar_name ([type]): [description]
        data_dn ([type]): [description]
        lidar_config_fn ([type], optional): [description]. Defaults to None.
        lidar_raw_iletter ([type], optional): [description]. Defaults to None.
        lidar_config_dn ([type], optional): [description]. Defaults to None.
    """

    if lidar_name in LIDAR_NAMES:
        lidar_setup = {}
    
        # nicklidar and config labels
        lidar_setup['lidar_name'] = lidar_name
        lidar_setup['nicklidar'] = LIDAR_INFO[lidar_name]['nick']
        lidar_setup['configs'] = {}
        # raw data directory
        lidar_setup['raw_data_dn'] = os.path.join(data_dn, lidar_name, '0a')
        if not check_dir(lidar_setup['raw_data_dn']):
            logger.error("Folder %s does not exist or not writable. Exit" % lidar_setup['raw_data_dn'])
            sys.exit(1)
        # L1 data directory
        lidar_setup['l1_data_dn'] = os.path.join(data_dn, lidar_name, '1a')
        if not check_dir(lidar_setup['l1_data_dn']):
            logger.error("Folder %s does not exist or not writable. Exit" % lidar_setup['l1_data_dn'])
            sys.exit(1)
        # Lidar Config Ini File
        if lidar_config_prod_fn is None:  # READ DEAFULT VALUES
            if lidar_config_dn is not None:
                for cl in LIDAR_INFO[lidar_name]['conf_labels']:
                    if lidar_name == "ALHAMBRA":
                        clfn = os.path.join(lidar_config_dn, "conf_prod_%s_%s.ini" % (lidar_name, cl))
                    else:
                        clfn = os.path.join(lidar_config_dn, "conf_prod_%s.ini" % lidar_name)
                    if os.path.isfile(clfn):
                        lidar_setup['configs'][cl] = clfn
                    else:
                        logger.error("Lidar Config File %s does not exist. Exit" % clfn)
                        sys.exit(1)
            else:
                logger.error("Directory of Lidar Config File cannot be None. Exit" % lidar_config_dn)
                sys.exit(1)
        else:  # USER-DEFINED
            if os.path.isfile(lidar_config_prod_fn):
                lidar_setup['configs']['user-defined'] = lidar_config_prod_fn
            else:
                logger.error("Lidar Config File %s does not exist. Exit" % lidar_config_prod_fn)
                sys.exit(1)
        # Initial Letter for Raw Files
        if lidar_raw_iletter is None:
            lidar_setup['lidar_raw_iletter'] = "R"
        else:
            lidar_setup['lidar_raw_iletter'] = lidar_raw_iletter
    else:
        logger.error("Lidar %s does not exist. Exit" % lidar_name)
        sys.exit()

    return lidar_setup


def set_raw_file_pttn(lidar_raw_iletter, date_str):
    """
    Build Raw File Pattern
    """

    yyyy = date_str[:4]
    yy = date_str[2:4]
    mm = date_str[4:6]
    mx = format(int(mm), 'X') 
    dd = date_str[6:8]
    return "%s*%s%s%s??.*" % (lidar_raw_iletter, yy, mx, dd)

    
def set_meas_folder_pttn(meas_type, date_str):
    """
    Build Measurement Folder Pattern
    """
    yyyy = date_str[:4]
    yy = date_str[2:4]
    mm = date_str[4:6]
    dd = date_str[6:8]
    if meas_type in ['ZS','AS']:
       meas_folder_pttn = "%s*_%s%s%s-*" % (meas_type, yy, mm, dd)
    else:
       meas_folder_pttn = "%s_%s%s%s_*" % (meas_type, yyyy, mm, dd)

    return meas_folder_pttn


def set_raw_file_fullpath_pttn(raw_data_dn, date_str, meas_dir_pttn, raw_file_pttn):
    """
    Build Full Path for Raw Files Pattern
    """
    yyyy = date_str[:4]
    mm = date_str[4:6]
    dd = date_str[6:8]
    return os.path.join(raw_data_dn, yyyy, mm, dd, meas_dir_pttn, raw_file_pttn)


def set_dir_fullpath_pttn(raw_data_dn, date_str, meas_dir_pttn):
    """
    Build Full Path for Raw Files Pattern
    """
    yyyy = date_str[:4]
    mm = date_str[4:6]
    dd = date_str[6:8]
    return os.path.join(raw_data_dn, yyyy, mm, dd, meas_dir_pttn)


def get_meas_dir_date(meas_dir):
    """
    Get Date (str) YYYYMMDD_HHMM from measurement folder
    Assumed format: MEASTYPE_YYYYMMDD_HHMM
    """

    if meas_dir[-1] == '/':
        meas_dir = meas_dir[:-1]

    return '_'.join(os.path.basename(meas_dir).split('_')[1:])


def prepare_L1a_output(nc_fullpath):
    """

    """
    nc_dn = os.path.dirname(nc_fullpath)
    nc_fn = os.path.basename(nc_fullpath)
    # Remove 1a Netcdf if overwrite
    if os.path.isfile(nc_fullpath):
        logger.info("Write file %s" % nc_fn)
        shutil.copyfile(nc_fullpath, "%s.%s" % (nc_fullpath, dt.datetime.utcnow().strftime("%Y%m%d_%H%M")))
    # Create folder if it does not exist
    if not check_dir(nc_dn):
        os.makedirs(nc_dn)


def run_raw2l1_daylike(raw2l1_py, lidar_setup, meas_type, date_str, overwrite=False):
    """
    Run Raw2L1 for daylike measurements: RS, OT, HF
    """

    logger.info("Start Run Raw2l1 for Daylike Measurement")

    # L1a Output Directory:
    nc_dn = os.path.join(lidar_setup['l1_data_dn'], date_str[:4], date_str[4:6], date_str[6:8]) 

    # Build Raw File Pattern
    raw_file_pttn = set_raw_file_pttn(lidar_setup['lidar_raw_iletter'], date_str)

    """ Loop over Configs
    """
    for lc in lidar_setup['configs']:
        # Conf Prod Ini File
        conf_prod_fn = lidar_setup['configs'][lc]
        logger.info("Config File: {}".format(conf_prod_fn))
    
        """ Fullpath for Netcdf (1a) """
        nc_fn = "{}_1a_P{}_{}_{}.nc".format(lidar_setup['nicklidar'], meas_type.lower(), lc, date_str)
        nc_fullpath = os.path.join(nc_dn, nc_fn)
    
        """ Check Run: Netcdf Exists """
        if np.logical_and(os.path.isfile(nc_fullpath), not overwrite):
            logger.info("File %s already exists and will not be overwritten" % nc_fn)
        else:
            """ List of raw files """
            # Loop over [day - 1, day]
            date_dt = dt.datetime.strptime(date_str, '%Y%m%d')
            date_range = pd.date_range(date_dt + dt.timedelta(days=-1), date_dt)
            raw_files_list = []
            for i_date in date_range:
                i_date_str = i_date.strftime('%Y%m%d')
                logger.info("Search files at %s" % i_date_str)
                # Build Pattern for Measurement Folder
                meas_dir_pttn = set_meas_folder_pttn(meas_type, i_date_str)
                # Build Full Pattern
                full_path_pttn = set_raw_file_fullpath_pttn(lidar_setup['raw_data_dn'], i_date_str, meas_dir_pttn, raw_file_pttn)
                raw_files_list.extend(sorted(glob.glob(full_path_pttn)))
            """ Exe Raw2l1 """
            if len(raw_files_list) > 0:
                # Prepare L1a output
                prepare_L1a_output(nc_fullpath)
                # Exe RAW2L1
                exe_raw2l1(raw2l1_py, date_str, conf_prod_fn, raw_files_list, nc_fullpath)
            else:
                logger.error("No Raw Files for %s and %s. Exit" % (meas_type, date_str))

    # Delete *part* files
    try:
        xx = glob.glob(os.path.join(nc_dn, '*part*'))
        for x in xx:
            os.remove(x)
    except:
        logger.warning("part files not deleted.")

    logger.info("End Run Raw2l1 for Daylike Measurement")


def run_raw2l1_folderlike(raw2l1_py, lidar_setup, meas_type, date_str, overwrite=False):
    """
    Run Raw2L1 for folderlike measurements: DC, TC, DP
    """

    logger.info("Start Run Raw2l1 for Type {} (Folderlike Measurement)".format(meas_type))

    # L1a Output Directory:
    nc_dn = os.path.join(lidar_setup['l1_data_dn'], date_str[:4], date_str[4:6], date_str[6:8]) 

    # Build Raw File Pattern
    raw_file_pttn = set_raw_file_pttn(lidar_setup['lidar_raw_iletter'], date_str)

    logger.info("Search files at %s" % date_str)
    """ List of Folders within the date """
    # Build Full Pattern for Measurement Folder
    meas_dir_pttn = set_meas_folder_pttn(meas_type, date_str)
    full_path_dir_pttn = set_dir_fullpath_pttn(lidar_setup['raw_data_dn'], date_str, meas_dir_pttn)
    # pdb.set_trace()
    meas_dir_list = sorted(glob.glob(full_path_dir_pttn))
    # pdb.set_trace()

    if len(meas_dir_list) > 0:
        """ Subtypes? """
        if meas_type in MEASUREMENT_SUBTYPES.keys():
            sub_types = MEASUREMENT_SUBTYPES[meas_type]
        else:
            sub_types = []

        """ Loop over Raw Measurement Folders
        """
        for meas_dn in meas_dir_list:
            logger.info("Start Process Measurement Folder: {}".format(meas_dn))
            # YYYYMMDD_HHMM
            meas_datetime = get_meas_dir_date(meas_dn)
            """ Subtyping
            """
            if len(sub_types) > 0:  # subtypes (TC, DP)
                """ Loop over Subtypes """
                for sub_type in sub_types:
                    logger.info("Start Process Sub-Type {}".format(sub_type))
                    """ Loop Over Configs """
                    for lc in lidar_setup['configs']:
                        # Conf Prod Ini File
                        conf_prod_fn = lidar_setup['configs'][lc]
                        logger.info("Config File: {}".format(conf_prod_fn))
                        """ Fullpath for Netcdf (1a) """
                        nc_fn = "{}_1a_P{}_{}_{}.nc".format(lidar_setup['nicklidar'], "%s-%s" % (meas_type.lower(), sub_type), lc, meas_datetime)
                        nc_fullpath = os.path.join(nc_dn, nc_fn)
    
                        """ Check RUN """
                        if np.logical_and(os.path.isfile(nc_fullpath), not overwrite):
                            logger.info("File %s already exists and will not be overwritten" % nc_fn)
                        else:
                            """ List of Raw Files """
                            sub_meas_dn = os.path.join(meas_dn, sub_type)
                            if os.path.isdir(sub_meas_dn):
                                # Build Full Pattern for Raw Files
                                full_path_pttn = set_raw_file_fullpath_pttn(lidar_setup['raw_data_dn'], \
                                        date_str, sub_meas_dn, raw_file_pttn)
                                raw_files_list = sorted(glob.glob(full_path_pttn))
                                if len(raw_files_list) > 0:
                                    # Prepare L1a output
                                    prepare_L1a_output(nc_fullpath)
                                    # Exe RAW2L1
                                    exe_raw2l1(raw2l1_py, date_str, conf_prod_fn, raw_files_list, nc_fullpath)
                                else:
                                    logger.error("No Raw Files for %s and %s" % (meas_type, date_str))
                            else:
                                logger.error("Subtype %s not found in measurement folder %s." % (sub_type, meas_dn))
                    logger.info("End Process Sub-Type {}".format(sub_type))
            else:  # No subtypes (DC) 
                """ Loop Over Configs """
                for lc in lidar_setup['configs']:
                    # Conf Prod Ini File
                    conf_prod_fn = lidar_setup['configs'][lc]
                    logger.info("Config File: {}".format(conf_prod_fn))
                    """ Fullpath for Netcdf (1a) """
                    nc_fn = "{}_1a_P{}_{}_{}.nc".format(lidar_setup['nicklidar'], meas_type.lower(), lc, meas_datetime)
                    nc_fullpath = os.path.join(nc_dn, nc_fn)
                    """ Check RUN """
                    if np.logical_and(os.path.isfile(nc_fullpath), not overwrite):
                        logger.info("File %s already exists and will not be overwritten. Exit" % nc_fn)
                    else:
                        """ List of raw files """
                        # Build Full Pattern for Raw Files
                        full_path_pttn = set_raw_file_fullpath_pttn(lidar_setup['raw_data_dn'], date_str, meas_dn, raw_file_pttn)
                        raw_files_list = glob.glob(full_path_pttn)
                        if len(raw_files_list) > 0:
                            # Prepare L1a output
                            prepare_L1a_output(nc_fullpath)
                            # Exe RAW2L1
                            exe_raw2l1(raw2l1_py, date_str, conf_prod_fn, raw_files_list, nc_fullpath)
                        else:
                            logger.error("No Raw Files for %s and %s" % (meas_type, date_str))
            logger.info("End Process Measurement Folder: {}".format(meas_dn))
    else:
        logger.error("No Folder(s) for %s and %s. Exit" % (meas_type, date_str))

    # Delete *part* files
    try:
        xx = glob.glob(os.path.join(nc_dn, '*part*'))
        for x in xx:
            os.remove(x)
    except:
        logger.warning("part files not deleted.")

    logger.info("End Run Raw2l1 for Type {} (Folderlike Measurement)".format(meas_type))

def run_raw2l1(raw2l1_py, lidar_setup, meas_type, date_str, overwrite=False):
    """
    Run RAW2L1
    
    for a particular lidar
    for a measurement type
    for a date

    """

    """ RAW2L1 particularized to Measurement Types """
    if meas_type in MEASUREMENT_TYPES_DAYLIKE:
        run_raw2l1_daylike(raw2l1_py, lidar_setup, meas_type, date_str, overwrite=overwrite)
        run_raw2l1_folderlike(raw2l1_py, lidar_setup, 'DC', date_str, overwrite=overwrite)
    elif meas_type in MEASUREMENT_TYPES_FOLDERLIKE:
        run_raw2l1_folderlike(raw2l1_py, lidar_setup, meas_type, date_str, overwrite=overwrite)
        if meas_type != 'DC':
            run_raw2l1_folderlike(raw2l1_py, lidar_setup, 'DC', date_str, overwrite=overwrite)
    elif meas_type in MEASUREMENT_TYPES_Scan:
        run_raw2l1_folderlike(raw2l1_py, lidar_setup, meas_type, date_str, overwrite=overwrite)
        run_raw2l1_folderlike(raw2l1_py, lidar_setup, 'DC', date_str, overwrite=overwrite)
    else:
        logger.error("Meas. Type %s not recognized. Exit" % meas_type)


def exe_raw2l1(raw2l1_py, date_str, lidar_config, raw_files_list, nc_output):
    """
    Python call to raw2l1
    """
    logger.info("Start Exe RAW2L1")

    """ Split Raw2L1 process in 60-file packages """
    # Join Files List in a single string
    #raw_files_list = [x.replace(lidar_setup['raw_data_dn'], r".") for x in raw_files_list]
    nf = len(raw_files_list)
    step = 5
    # step = 60
    nc_fns = []
    for i in range(0, nf, step):
        raw_files_list_str = ' '.join(raw_files_list[i:(i+step)])
        nc_fn = "{}.part_{}".format(nc_output, i)
        #working_dn = os.getcwd()
        #os.chdir(lidar_setup['raw_data_dn'])
        #os.chdir(working_dn)
        python_exe = sys.executable
        cmd = "%s %s %s %s %s %s" % (python_exe, raw2l1_py, date_str, lidar_config, raw_files_list_str, nc_fn) 
        # pdb.set_trace()

        try:
            print(cmd)
            #os.system(cmd)
            p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            nc_fns.append(nc_fn)
        except Exception as e:
            logger.error(str(e))
            logger.error(cmd)
    """ Concatenate Netcdf Files """
    if len(nc_fns) > 0:
        ds = None
        for nc_fn in nc_fns:
            if os.path.isfile(nc_fn):
                try:
                    with xr.open_dataset(nc_fn) as dsi:
                        if ds is None:
                            ds = dsi
                        else:
                            ds = xr.concat([ds, dsi], dim='time', data_vars='minimal', coords='minimal', compat='override')
                except:
                    logger.critical("File {} not concatenated".format(nc_fn))
        if ds is not None:
            ds.to_netcdf(nc_output)
        else:
            logger.critical("Dataset is None. Netcdf File not generated")

    logger.info("End Exe RAW2L1")


def parse_args():
    """
    Parse Input Arguments
    """
    parser = argparse.ArgumentParser(description="usage %prog [arguments]")

    parser.add_argument("-l", "--lidar",
        action="store",
        dest="lidar_name",
        required=True,
        help="Lidar Name [MULHACEN, VELETA].")
    parser.add_argument("-i", "--initial_date",
        action="store",
        dest="date_ini_str",
        required=False,
        help="Initial date [example: '20190131'].")
    parser.add_argument("-e", "--final_date",
        action="store",
        dest="date_end_str", 
        required=False,
        help="Final date [example: '20190131'].")
    parser.add_argument("-t", "--measurement_type",
        action="store",
        dest="meas_type",
        required=True,
        help="Type of measurement [example: 'RS', 'HF'].")
    parser.add_argument("-c", "--lidar_config_prod",
        action="store",
        dest="lidar_config_prod_fn",
        required=False,
        default=None,
        help="[OPTIONAL] Lidar Config Prod Ini File [see /[code]/raw2l1_v2/raw2l1/conf/config_prod_MULHACEN.ini].")
    parser.add_argument("-x", "--iletter",
        action="store",
        dest="lidar_raw_iletter",
        required=False,
        default=None,
        help="[OPTIONAL] Lidar Initial Raw Letter")
    parser.add_argument("-y", "--config",
        action="store",
        dest="config_fn",
        required=False,
        default=None,
        help="[OPTIONAL] Yaml File with Configuration Information: python interpreter, raw2l1 package, logging directory, data directory. [DEFAULT: config/config_server.yaml].")
    parser.add_argument("-w", "--overwrite",
        action="store",
        dest="overwrite",
        required=False,
        default=False,
        help="[OPTIONAL] Overwrite 1a netcdf file if exists.")
    parser.add_argument("-r", "--raw2l1",
        action="store",
        dest="raw2l1",
        required=False,
        default=None,
        help="[OPTIONAL] Full Path for raw2l1.py")
    parser.add_argument("-d", "--data_dn",
        action="store",
        dest="data_dn",
        required=False,
        default=None,
        help="[OPTIONAL] Full Path for data directory")

    args = parser.parse_args()
    return args.__dict__


def lidar_raw2l1():
    """
    Main Script
    """
    logger.info("Start RAW2L1: %s" % dt.datetime.utcnow().strftime("%Y%m%d_%H%M"))

    """ parse args """
    args = parse_args()

    # Set date end
    # if args['date_end_str'] is None:
    #     args['date_end_str'] = args['date_ini_str']
    if  np.logical_and (args['date_ini_str'] is None,args['date_end_str'] is None):
        args['date_ini_str']  =(datetime.now()-timedelta(days=1)).strftime('%Y%m%d')
        args['date_end_str'] = datetime.now().strftime('%Y%m%d')
    elif args['date_end_str']  is None:
        args['date_end_str']  = args['date_ini_str']
    # Check Meas Type 
    check_measurement_type(args['meas_type'])
    # Overwrite
    if isinstance(args['overwrite'], str):
        if args['overwrite'] in ['True', 'true', 'TRUE']:
            args['overwrite'] = True
        elif args['overwrite'] in ['False', 'false', 'FALSE']:
            args['overwrite'] = False
        else:
            args['overwrite'] = False

    """ read config for lidar_raw2l1 """
    config = read_config(args['config_fn'])
    if args['raw2l1'] is not None:
        raw2l1_py = args['raw2l1']
    else:
        raw2l1_py = config['raw2l1_py']
    if args['data_dn'] is not None:
        data_dn = args['data_dn']
    else:
        data_dn = config['data_dn']
    # pdb.set_trace()
    raw2l1_dn = os.path.dirname(raw2l1_py)

    """ setup lidar info """
    # set lidar config file directory if no lidar config file is given
    lidar_config_dn = None
    if args['lidar_config_prod_fn'] is None:
        lidar_config_dn = os.path.join(raw2l1_dn, 'conf')
    lidar_setup = setup_lidar(args['lidar_name'], data_dn, lidar_config_prod_fn=args['lidar_config_prod_fn'], \
            lidar_raw_iletter=args['lidar_raw_iletter'], lidar_config_dn=lidar_config_dn)

    """ Run RAW2L1 """
    date_range = pd.date_range(args['date_ini_str'], args['date_end_str'])
    for i_date in date_range:
        i_date_str = i_date.strftime('%Y%m%d')
        run_raw2l1(raw2l1_py, lidar_setup, args['meas_type'], i_date_str, overwrite=args['overwrite'])

    logger.info("End RAW2L1: %s" % dt.datetime.utcnow().strftime("%Y%m%d_%H%M"))


if __name__ == "__main__":
    lidar_raw2l1()