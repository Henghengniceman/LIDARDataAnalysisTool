"""
Generic Reader for Lidar

"""

from __future__ import print_function, absolute_import, division

import os
import sys
import ast
import datetime as dt
from collections import OrderedDict
from telnetlib import SUPPRESS_LOCAL_ECHO
from tkinter import W
from traceback import format_exc
from matplotlib import scale

import numpy as np
import netCDF4 as nc
#from pydantic import EnumMemberError
from scipy import stats
import pdb
import time


"""
General info
"""
DATETIME_FMT = '{} {}'
DATE_FMT = '%d/%m/%Y %H:%M:%S'
TIME_FMT = '%H:%M:%S'

N_HEADER_LINE = 3

N_HEADER_LINE_Scan = 4

MISSING_FLOAT = np.nan
MISSING_INT = -9

# POLARIZATION STATES
POLARIZATION = {
    'o': 0,
    'p': 1,
    's': 2
}

# DETECTION MODES
DETECTION_MODES = {
    'analog': 0,
    'photoncounting': 1,
    'laser_power': 2
}


# Background Things
BCK_MIN_ALT_KEY = 'bckgrd_min_alt'  # field name in .ini [reader_conf]
BCK_MAX_ALT_KEY = 'bckgrd_max_alt'
BCK_COMMENT_FMT = 'calcultated between {:5d} m and {:5d} m'

"""
LIDAR SPECIFIC INFO
- DEFAULT_RESOLUTION: spatial resolution given by the default configuration of the licel
- BCK_MIN_ALT: lower limit for bckgrd calculation
- BCK_MAX_ALT: upper limit for bckgrd calculation
- CHANNELS: list of all channels installed in lidar
"""
LIDAR_SYSTEMS = ['VELETA', 'MULHACEN', 'ALHAMBRA','KASCAL']
LIDAR_INFO = {
    'MULHACEN':{
        'DEFAULT_RESOLUTION': 7.5,
        'BCK_MIN_ALT': 75000,
        'BCK_MAX_ALT': 105000,
        'CHANNELS': {'BT0': '532xpa',   'BC0': '532xpp', 
                     'BT1': '532xsa',   'BC1': '532xsp', 
                     'BT2': '355xta',   'BC2': '355xtp', 
                     'BT3': '1064xta',  'BC3': '607xtp', 
                                        'BC4': '387xtp',
                                        'BC5': '408xtp'}
    },
    'VELETA':{
        'DEFAULT_RESOLUTION': 7.5,
        'BCK_MIN_ALT': 75000,
        'BCK_MAX_ALT': 105000,
        'CHANNELS': {'BT0': '355xpa',   'BC0': '355xpp', 
                     'BT1': '355xsa',   'BC1': '355xsp', 
                     'BT2': '387xta',   'BC2': '387xtp'}
    
    },
    'KASCAL':{
        'DEFAULT_RESOLUTION': 7.5,
        'BCK_MIN_ALT': 75000,
        'BCK_MAX_ALT': 105000,
        'CHANNELS': {'BT0': '355xpa',   'BC0': '355xpp', 
                     'BT1': '355xsa',   'BC1': '355xsp', 
                     'BT2': '387xta',   'BC2': '387xtp'}
    
    },
    'ALHAMBRA':{
        'DEFAULT_RESOLUTION': 7.5,
        'BCK_MIN_ALT': 50000,
        'BCK_MAX_ALT': 60000,
        'CHANNELS': {'BT0': '1064fta',  'S2A0': '1064fta', 
                     'BT1': '1061fta',  'S2A1': '1061fta', 
                     'BT2': '532fta',   'S2A2': '532fta',   'BC2': '532ftp',  'S2P2': '532ftp', 
                     'BT3': '531fta',   'S2A3': '531fta',   'BC3': '531ftp',  'S2P3': '531ftp',
                     'BT4': '355fpa',   'S2A4': '355fpa',   'BC4': '355fpp',  'S2P4': '355fpp',
                     'BT5': '355fsa',   'S2A5': '355fsa',   'BC5': '355fsp',  'S2P5': '355fsp',
                     'BT6': '354fta',   'S2A6': '354fta',   'BC6': '354ftp',  'S2P6': '354ftp',
                     'BT7': '408fta',   'S2A7': '408fta',   'BC7': '408ftp',  'S2P7': '408ftp',
                     'BT10': '1064nta', 'S2A10': '1064nta',
                     'BT11': '532npa',  'S2A11': '532npa',  'BC11': '532npp', 'S2P11': '532npp',
                     'BT12': '532nsa',  'S2A12': '532nsa',  'BC12': '532nsp', 'S2P12': '532nsp',
                     'BT13': '355npa',  'S2A13': '355npa',  'BC13': '355npp', 'S2P13': '355npp',
                     'BT14': '355nsa',  'S2A14': '355nsa',  'BC14': '355nsp', 'S2P14': '355nsp',
                     'BT15': '387nta',  'S2A15': '387nta',  'BC15': '387ntp', 'S2P15': '387ntp',
                     'BT16': '607nta',  'S2A16': '607nta', 
                     'PD00': 'pd00',    'PD01': 'pd01'}
    }
}


def date_to_dt(date_num, date_units):
    """convert date np.array from datenum to datetime.datetime 

    Args:
        date_num ([type]): [description]
        date_units ([type]): [description]
    """
    return nc.num2date(date_num,
                       units=date_units,
                       calendar='standard')


def get_bck_alt(lidar_system, conf, logger):
    """get value of maximum and minimum altitude for background signal calculation
    if not define, use default value"""

    try:
        min_alt = ast.literal_eval(conf[BCK_MIN_ALT_KEY])
    except KeyError:
        min_alt = LIDAR_INFO[lidar_system]['BCK_MIN_ALT']
        logger.warning('%s not defined in conf file. Using default value %d',
                       BCK_MIN_ALT_KEY, min_alt)
    except ValueError:
        logger.critical("error parsing '%s' option in [reader_conf] in config file. quitting",
                        BCK_MIN_ALT_KEY, conf[BCK_MIN_ALT_KEY])
        sys.exit(1)

    try:
        max_alt = ast.literal_eval(conf[BCK_MAX_ALT_KEY])
    except KeyError:
        max_alt = LIDAR_INFO[lidar_system]['BCK_MAX_ALT']
        logger.warning('%s not defined in conf file. Using default value %d',
                       BCK_MAX_ALT_KEY, max_alt)
    except ValueError:
        logger.critical("error parsing '%s' option in [reader_conf] in config file. quitting",
                        BCK_MAX_ALT_KEY, conf[BCK_MAX_ALT_KEY])
        sys.exit(1)

    return min_alt, max_alt


def get_lidar_config(config, logger):
    """ Get Lidar Config Info

    Args:
        conf ([type]): [description]
        logger ([type]): [description]
    """
    lidar_config = {}

    """ Lidar System
    """
    try:
        lidar_system = config['system']
        if not lidar_system in LIDAR_SYSTEMS:
            logger.critical("Lidar System %s Found. Exit" % lidar_system)
            sys.exit(1)
    except Exception as e:
        logger.critical(str(e))
        logger.critical("No Lidar System Found. Exit")
        sys.exit(1)

    """ Lidar Channels
    """
    # channels expected
    lidar_channels_id = [*LIDAR_INFO[lidar_system]['CHANNELS'].keys()]
    lidar_channels_name = [*LIDAR_INFO[lidar_system]['CHANNELS'].values()]
    lidar_channels_number = np.arange(len(lidar_channels_id))
    try:
        config_channels_id = ast.literal_eval(config['channels'])
    except ValueError:
        logger.critical("error parsing 'channels' option in [reader_conf] in config file. quitting")
        sys.exit(1)
    # check expected channels in lidar channels
    if all([cc in lidar_channels_id for cc in config_channels_id]):
        config_channels_number = np.array([lidar_channels_number[lidar_channels_id.index(c)] \
            for c in config_channels_id])
        config_channels_name = [lidar_channels_name[lidar_channels_id.index(c)] \
            for c in config_channels_id]
    else:
        logger.critical("Wrong Channel Name in Config file. Exit")
        sys.exit(1)
    
    if all(['B' in c for c in config_channels_id]):
        channels_type = 'rs'
    elif all(['S' in c for c in config_channels_id]):
        channels_type = 'sd'
    elif all(['P' in c for c in config_channels_id]):
        channels_type = 'pd'
    else:
        logger.critical("Error in Channels Configuration. Check config.ini file")
        sys.exit(1)

    """ Lidar Config
    """
    lidar_config['lidar_system'] = lidar_system
    lidar_config['channels_id'] = config_channels_id
    lidar_config['channels_name'] = config_channels_name 
    lidar_config['channels_number'] = config_channels_number
    lidar_config['channels_type'] = channels_type

    return lidar_config


def check_time_spatial_dimensions(file_, config_channels_id, channels_type, logger):
    """ Check if channels in bin share same num bins (except photodiode channels in alhambra)

    Args:
        file_ ([type]): [description]
        config_channels_id ([type]): [description]
        channels_type ([type]): [description]
        logger ([type]): [description]
    """

    try:
        fid = open(file_, 'rb')
    except IOError:
        logger.error("error trying to open %s", file_)
    # pdb.set_trace()
    # read part of the header that provides info on timestamp, channels and num bins
    fid.readline()

    # line 2 : date and time, we need it
    line = fid.readline()
    if isinstance(line, bytes):
        line = line.decode("utf-8")
    elts = line.split()
    datetime_str = DATETIME_FMT.format(elts[1], elts[2])

    # try to parse date to check file is valid
    try:
        timestamp = dt.datetime.strptime(datetime_str, DATE_FMT)
    except ValueError:
        logger.error("wrong time format in " + file_)
        timestamp = False
        
        
    if file_.split('\\')[-2][0:2] in ['ZS','AS']:
        line = fid.readline()
    line = fid.readline()
    if isinstance(line, bytes):
        line = line.decode("utf-8")
    elts = line.split()
    num_datasets = int(elts[4])
    spatial_dim_arr = np.zeros(len(config_channels_id))*np.nan
    num_bins_arr = np.zeros(num_datasets)
    bin_channels_id = ['']*num_datasets
    for i in range(num_datasets):
        line = fid.readline()
        if isinstance(line, bytes):
            line = line.decode("utf-8")
        elts = line.split()
        num_bins_arr[i] = float(elts[3])
        bin_channels_id[i] = elts[15]
    fid.close()

    # check num bins along channels
    for i, c in enumerate(config_channels_id):
        if c in bin_channels_id:
            spatial_dim_arr[i] = num_bins_arr[bin_channels_id.index(c)]
    num_bins = np.unique(spatial_dim_arr[~np.isnan(spatial_dim_arr)])
    
    # if timestamp is correct and num_bins is coherent, ok
    ok_t = False
    if timestamp:
        ok_t = True
    ok_s = False
    if len(num_bins) == 1:
        ok_s = True
    else:
        if channels_type == 'pd':
            ok_s = True

    if ok_t and ok_s:
        dim_t = 1
        dim_s = num_bins
    else:
        dim_t = 0
        dim_s = []
    return dim_t, dim_s


def get_data_size(list_files, lidar_system, config_channels_id, channels_type, logger):
    """[summary]

    Args:
        list_files ([type]): [description]
        lidar_system ([type]): [description]
        config_channels_id ([type]): [description]
        channels_type ([type]): [description]
        logger ([type]): [description]
    """
    # Initialize dimensions
    data_dim = {}

    """ Get Channels Dimension """
    dim_c = len(config_channels_id)
    logger.info('number of channels : %d', dim_c)

    """ Check Time and Spatial Dimension """
    list_files_2 = []
    flag_t = []
    flag_s = []
    for _, file_ in enumerate(list_files):
        i_t, i_s = check_time_spatial_dimensions(file_, config_channels_id, channels_type, logger)
        flag_t.append(i_t)
        flag_s.append(i_s)
    flag_t = np.array(flag_t)
    flag_s = np.array(flag_s)
    if channels_type != 'pd': # RCS, STD: RANGE
    #if dim_s.shape[1] == 1:
        dim_r = int(stats.mode(flag_s.ravel()).mode)
        for i, file_ in enumerate(list_files):
            if np.logical_and(flag_t[i] == 1, flag_s[i] == dim_r):
                list_files_2.append(file_)
    else: # PD
        for i, file_ in enumerate(list_files):
            if flag_t[i] == 1:
                list_files_2.append(file_)
        if lidar_system == 'ALHAMBRA':
            # set dimensions for pd
            dim_pd0, dim_pd1 = 600, 1200
        else:
            logger.critical("lidar system %s does not laser count dimension. Exit" % lidar_system)
            sys.exit(1)
    dim_t = len(list_files_2)    

    """ Setting dimensions """
    data_dim['time'] = dim_t
    data_dim['channel'] = dim_c
    if channels_type == 'pd': # PD
        if lidar_system == 'ALHAMBRA':
            data_dim['n_pd0'] = dim_pd0
            data_dim['n_pd1'] = dim_pd1
        else:
            logger.critical("lidar system %s does not laser count dimension. Exit" % lidar_system)
            sys.exit(1)
    else: # RCS, STD
        data_dim['range'] = dim_r

    return data_dim, list_files_2


def read_header(fid, logger):
    """[summary]

    Args:
        fid ([type]): [description]
        logger ([type]): [description]
    """

    logger.debug('Start Reading Header')
    header = {}

    # point at beginning
    fid.seek(0)

    # First Line is File Name
    logger.debug('First Line')
    line = fid.readline()
    if isinstance(line, bytes):
        line = line.decode("utf-8")
    header['file_name'] = line.split()[0]

    # Second Line: spatio-temporal info
    logger.debug('Second Line')
    line = fid.readline()
    if isinstance(line, bytes):
        line = line.decode("utf-8")
    elts = line.split()
    if len(elts) >= 10: # ALHAMBRA
        header['location'] = elts[0]
        header['datetime_start'] = DATETIME_FMT.format(elts[1], elts[2])
        header['datetime_end'] = DATETIME_FMT.format(elts[3], elts[4])
        header['altitude'] = float(elts[5])
        header['longitude'] = float(elts[6])
        header['latitude'] = float(elts[7])
        header['zenith'] = float(elts[8])
        header['azimuth'] = float(elts[9])
    elif len(elts) == 12: # VELETA, MULHACEN
        header['temperature'] = float(elts[10])
        header['pressure'] = float(elts[11])
    else:
        logger.critical("Line 2 has different elements than expected. Exit")
        sys.exit(1)

    # Third Line: Laser, Num Dataset Info
    # pdb.set_trace()
    if fid.name.split('\\')[-2][0:2] in ['ZS','AS']:
        line = fid.readline()
    
    logger.debug('Third Line')
    line = fid.readline()
    if isinstance(line, bytes):
        line = line.decode("utf-8")
    elts = line.split()
    header['laser_1_num_shots'] = int(elts[0])
    header['laser_1_pulse_frequency'] = int(elts[1])
    header['laser_2_num_shots'] = int(elts[2])
    header['laser_2_pulse_frequency'] = int(elts[3])
    header['num_datasets'] = int(elts[4])
    # rest of elts are not important so far

    # Dataset Info
    logger.debug('Dataset Info')
    channels_info = {}
    for i in range(header['num_datasets']):
        line = fid.readline()
        if isinstance(line, bytes):
            line = line.decode("utf-8")
        elts = line.split()
        channel_description = {}
        channel_description['active'] = int(elts[0])
        channel_description['type'] = int(elts[1])
        channel_description['laser_source'] = int(elts[2])
        channel_description['num_bins'] = int(elts[3])
        channel_description['laser_polarization'] = int(elts[4])
        channel_description['pmt_voltage'] = int(elts[5])
        channel_description['bin_width'] = float(elts[6])
        channel_description['wavelength'] = int(elts[7].split('.')[0])
        channel_description['polarization'] = elts[7].split('.')[1]
        channel_description['powermeter'] = elts[8]
        channel_description['bin_shift_int'] = int(elts[10])
        channel_description['bin_shift_dec'] = int(elts[11])
        channel_description['ADC_bits'] = int(elts[12])
        channel_description['num_shots'] = int(elts[13])
        channel_description['adc_range_discriminator_level'] = float(elts[14])
        channel_description['channel_id'] = elts[15]
        if len(elts) >= 18:
            channel_description['channel_name_licel'] = elts[16].replace('"', '')
            channel_description['channel_name'] = elts[17].replace('"', '')
        else:
            channel_description['channel_name_licel'] = ''
            channel_description['channel_name'] = ''
        channels_info[elts[15]] = channel_description
    header['channels_info'] = channels_info
    logger.debug('End Reading Header')

    return header


def read_profiles(fid, header, logger):
    """[summary]

    Args:
        fid ([type]): [description]
        header ([type]): [description]
        logger ([type]): [description]
    """

    # beginning of file
    # pdb.set_trace()

    fid.seek(0)

    # skip header (ASCII part of the file)
    # pdb.set_trace()
    N_HEADER_LINE = 3
    N_HEADER_LINE_Scan = 4
    
    num_datasets = header['num_datasets']
    if fid.name.split('\\')[-2][0:2] in ['ZS','AS']:
        N_HEADER_LINE = N_HEADER_LINE_Scan
        
    lines_to_skip = N_HEADER_LINE + num_datasets + 1
    
    for i in range(lines_to_skip):
        fid.readline()

    # read profiles
    profiles = {}
    for i_chan in header['channels_info']:
        tmp_data = np.fromfile(fid, dtype='i4', count=\
            header['channels_info'][i_chan]['num_bins'])
        profiles[i_chan] = tmp_data
        fid.seek(fid.tell()+2)

    # end of file?
    eor = fid.tell()
    eof = fid.seek(0, 2)
    if eor != eof:
        logger.critical("EOF not reached. Wrong read. Exit")
        sys.exit(1)

    return profiles


def read_file(file_fn, channels_id, logger):
    """[summary]

    Args:
        file_fn ([type]): [description]
        logger ([type]): [description]
        channels_id ([type]): [description]
    """
    logger.info("reading %s", file_fn)
    try:
        fid = open(file_fn, 'rb')
        header = read_header(fid, logger)
        profiles = read_profiles(fid, header, logger)
        fid.close()
    
        # Subset header, profiles for channels according configuration
        new_profiles = {}
        new_channels_info = {}
        channels_info = header['channels_info']
        bin_channels_list = [*channels_info.keys()]
        for ch in channels_id:  # loop over config channels
            if ch in profiles.keys(): # check channel exists in bin file
                new_profiles[ch] = profiles[ch]
                ch_n = bin_channels_list[bin_channels_list.index(ch)]
                new_channels_info[ch] = header['channels_info'][ch_n]
            else:
                new_profiles[ch] = None
                new_channels_info[ch] = None

        # update header info: channels in config.
        header['channels_info'] = new_channels_info
        header['num_datasets'] = len(channels_id)
    
        # update profiles
        profiles = new_profiles
    except IOError:
        logger.error("error reading " + file_fn)
        header, profiles = None, None

    return header, profiles


def calculate_physical_magnitudes_analog(raw_data, num_shots, ADCrange, adc_bits):
    """ Analog Raw Data to mV

    Args:
        raw_data ([type]): [description]
        num_shots ([type]): [description]
        ADCrange ([type]): [description]
        adc_bits ([type]): [description]
    """

    # normalize with number of shots
    norm = raw_data / num_shots

    # scale factor
    scale_factor = ADCrange / (2**adc_bits - 1)

    data = norm * scale_factor
    # to mV
    data *= 1000 # mV
    units = 'mV'

    return data, units


def calculate_physical_magnitudes_photoncounting(raw_data, num_shots, default_resolution, bin_width):
    """ Photoncounting Raw Data to MHz

    Args:
        raw_data ([type]): [description]
        num_shots ([type]): [description]
        default_resolution ([type]): [description]
        bin_width ([type]): [description]
    """

    # normalize with number of shots
    norm = raw_data / num_shots

    # scale factor
    scale_factor = 20*default_resolution/bin_width

    data = norm * scale_factor 
    units = 'MHz'

    return data, units


def set_data(lidar_system, data, index, header, profiles, data_dim, \
    channels_type, channels_id, channels_name, logger):

    logger.info("Start set data for index=%i" % index)

    """ Initialize data: data = {}
    """
    if not data:
        logger.info("Initialize Data ...")
        logger.info("Type: %s" % channels_type)

        # Set Dimensions
        n_t = data_dim['time']
        n_c = data_dim['channel']
        if np.logical_or(channels_type == 'rs', channels_type == 'sd'):
            n_r = data_dim['range']
        elif channels_type == 'pd':
            if lidar_system == 'ALHAMBRA':
                n_pd0 = data_dim['n_pd0']
                n_pd1 = data_dim['n_pd1']
                laser_channel = {}
                for ch in channels_name:
                    if ch == 'pd00':
                        laser_number = 1
                        n_pd = n_pd0
                    elif ch == 'pd01':
                        laser_number = 2
                        n_pd = n_pd1
                    else:
                        logger.critical("Laser Channel %s Not Found. Exit" % ch)
                        sys.exit(1)
                    laser_channel[ch] = {}
                    laser_channel[ch]['laser_number'] = laser_number
                    laser_channel[ch]['dim_pd'] = n_pd
        else:
            logger.critical("Data Type %s not found. Exit" % channels_type)
            sys.exit(1)

        # Initialize Coordinates 
        data['time'] = np.empty((n_t,), dtype=np.dtype(dt.datetime))
        data['channel'] = np.empty((n_c,), dtype=np.str('<U10'))

        # SCALAR Variables supposed to be constant along files
        data['location'] = ''
        data['latitude'] = MISSING_FLOAT
        data['longitude'] = MISSING_FLOAT
        data['altitude'] = MISSING_FLOAT
        data['time_resol'] = MISSING_FLOAT
        data['range_resol'] = MISSING_FLOAT
        data['custom_comment'] = ''

        # Variables Channel-dependent
        data['channel_id'] = np.empty((n_c,), dtype=np.str('<U10'))
        #data['channel_name'] = np.empty((n_c,), dtype=np.str('<U10'))
        data['wavelength'] = np.ones((n_c,), dtype=np.int) * MISSING_FLOAT
        data['detection_mode'] = np.ones((n_c,), dtype=np.int) * MISSING_INT
        data['polarization'] = np.array(['o'] * n_c, dtype=np.str)
        data['dataset_type'] = np.ones((n_c,), dtype=np.int) * MISSING_INT
        data['laser_source'] = np.ones((n_c,), dtype=np.int) * MISSING_INT
        data['range_resol_vect'] = np.ones((n_c,), dtype=np.float32) * MISSING_FLOAT
        data['powermeter'] = np.ones((n_c,), dtype=np.float32) * MISSING_FLOAT
        data['laser_polarization'] = np.ones((n_c,), dtype=np.int)* MISSING_INT
        data['n_range'] = np.ones((n_c,), dtype=np.int) * MISSING_INT
        data['n_shots'] = np.ones((n_c,), dtype=np.int) * MISSING_INT
        data['telescope'] = np.ones((n_c,), dtype=np.int) * MISSING_INT

        data['bin_shift'] = np.ones((n_c,), dtype=np.int) * MISSING_INT
        data['bin_shift_dec'] = np.ones((n_c,), dtype=np.int) * MISSING_INT
        data['adc_bits'] = np.ones((n_c,), dtype=np.int) * MISSING_INT
        data['discriminator_level'] = np.ones((n_c,), dtype=np.int) * MISSING_FLOAT
        data['adc_range'] = np.ones((n_c,), dtype=np.float32) * MISSING_FLOAT
        data['field_14'] = np.ones((n_c,), dtype=np.float32) * MISSING_FLOAT
        data['number_one'] = np.ones((n_c,), dtype=np.int) * MISSING_INT

        # multi_dim vars
        data['active'] = np.zeros((n_t, n_c), dtype=np.int) * MISSING_INT
        data['voltage'] = np.ones((n_t, n_c), dtype=np.int) * MISSING_INT

        # Variables only Time-dependent
        data['n_chan_vector'] = np.ones((n_t,), dtype=np.int) * MISSING_INT
        data['zenith'] = np.ones((n_t,),) * MISSING_FLOAT
        data['azimuth'] = np.ones((n_t,)) * MISSING_FLOAT

        # Range dependent Variables: signal, std, photodiode
        if channels_type == 'rs':
            for ch in channels_name:
                data['signal_{:s}'.format(ch)] = np.ones((n_t, n_r,), dtype=np.float32) * MISSING_FLOAT
                data['units_signal_{:s}'.format(ch)] = ''
        elif channels_type == 'sd':
            for ch in channels_name:
                data['std_{:s}'.format(ch)] = np.ones((n_t, n_r,), dtype=np.float32) * MISSING_FLOAT
                data['units_std_{:s}'.format(ch)] = ''
        elif channels_type == 'pd':
            if lidar_system == 'ALHAMBRA':
                for ch in channels_name:
                    l_ch = laser_channel[ch]
                    data['laser_power_{:s}'.format(ch)] = \
                        np.ones((n_t, l_ch['dim_pd'],), dtype=np.float32) * MISSING_FLOAT
                    data['units_laser_power_{:s}'.format(ch)] = ''
        else:
            pass
        logger.info('... Done')
    
    """ Write in Data
    """
    # channels info from binary header
    channels_info = header['channels_info']

    """ Set Variables Independent on Time """
    if index == 0:
        data['location'] = header['location']
        data['latitude'] = header['latitude']
        data['longitude'] = header['longitude']
        data['altitude'] = header['altitude']
        data["laser1_shots"] = header['laser_1_num_shots']
        data['laser1_frequency'] = header['laser_1_pulse_frequency']
        data["laser2_shots"] = header['laser_2_num_shots']
        data['laser2_frequency'] = header['laser_2_pulse_frequency']
    
    """ Variables Time Dependent """
    data['n_chan_vector'][index] = header['num_datasets'] 
    data['zenith'][index] = header['zenith'] 
    data['azimuth'][index] = header['azimuth'] 

    """ Variables Channel (and Time) Dependent """
    for i_chan, ch in enumerate(channels_id):
        if index == 0:  # impepinable
            #data['channel'][i_chan] = channels_number[i_chan]
            data['channel'][i_chan] = channels_name[i_chan]
            data['channel_id'][i_chan] = channels_id[i_chan]
            #data['channel_name'][i_chan] = channels_name[i_chan]
        if channels_info[ch] is not None:
            data['active'][index, i_chan] = channels_info[ch]['active']
            data['voltage'][index, i_chan] = channels_info[ch]['pmt_voltage']
            if index == 0:
                data['dataset_type'][i_chan] = channels_info[ch]['type']
                data['laser_source'][i_chan] = channels_info[ch]['laser_source']
                data['telescope'][i_chan] = channels_info[ch]['laser_source']
                data['n_range'][i_chan] = channels_info[ch]['num_bins']
                data['laser_polarization'][i_chan] = channels_info[ch]['laser_polarization']
                data['range_resol_vect'][i_chan] = channels_info[ch]['bin_width']
                data['wavelength'][i_chan] = channels_info[ch]['wavelength']
                data['polarization'][i_chan] = channels_info[ch]['polarization']
                data['powermeter'][i_chan] = channels_info[ch]['powermeter']
    
                data['n_shots'][i_chan] = channels_info[ch]['num_shots']
                data['bin_shift'][i_chan] = channels_info[ch]['bin_shift_int']
                data['bin_shift_dec'][i_chan] = channels_info[ch]['bin_shift_dec']
                data['adc_bits'][i_chan] = channels_info[ch]['ADC_bits']
    
                # detection mode: analog, photoncounting, laser_power
                if data['dataset_type'][i_chan] == 0 or data['dataset_type'][i_chan] == 2:  # Analog 
                    data['detection_mode'][i_chan] = DETECTION_MODES['analog']
                    data['adc_range'][i_chan] = channels_info[ch]['adc_range_discriminator_level']
                elif data['dataset_type'][i_chan] == 1 or data['dataset_type'][i_chan] == 3:  # Photoncounting
                    data['detection_mode'][i_chan] = DETECTION_MODES['photoncounting']
                    data['discriminator_level'][i_chan] = channels_info[ch]['adc_range_discriminator_level']
                elif data['dataset_type'][i_chan] == 4:  # Laser Power
                    data['detection_mode'][i_chan] = DETECTION_MODES['laser_power']
                    data['field_14'][i_chan] = channels_info[ch]['adc_range_discriminator_level']
                else:
                    logger.critical("Data Type %s not recognized. Exit" % data['detection_mode'][i_chan])
                    sys.exit(1)

    # LIDAR RANGE RESOLUTION
    rrv = data['range_resol_vect'][~np.isnan(data['range_resol_vect'])]
    if len(np.unique(rrv)) == 1:
        data['range_resol'] = rrv[0]
    else:
        logger.critical("Range Resolution not the same in all profiles. Exit")
        sys.exit(1)
    
    # Assign Data Profiles
    if channels_type == 'rs':
        # Build signal variable
        for i_chan, ch in enumerate(channels_id):
            raw_data = profiles[ch] 
            if raw_data is not None:
                num_shots = data['n_shots'][i_chan]
                if data['dataset_type'][i_chan] == 0:  # ANALOG
                    signal_data, units = calculate_physical_magnitudes_analog(raw_data, num_shots, data['adc_range'][i_chan], data['adc_bits'][i_chan])
                    #signal_data, units = raw_data, ''
                elif data['dataset_type'][i_chan] == 1:  # PHOTONCOUNTING
                    signal_data, units = calculate_physical_magnitudes_photoncounting(raw_data, num_shots, LIDAR_INFO[lidar_system]['DEFAULT_RESOLUTION'], data['range_resol'])
                    #signal_data, units = raw_data, ''
                else:
                    logger.critical("Data Type %s not RS-type. Exit" % data['dataset_type'][i_chan])
                    sys.exit(1)
                data['signal_{:s}'.format(channels_name[i_chan])][index, :] = signal_data
                if index == 0:
                    data['units_signal_{:s}'.format(channels_name[i_chan])] = units
    elif channels_type == 'sd':
        #TODO: confirm with Raymetrics scale factors for physical units of STD
        for i_chan, ch in enumerate(channels_id):
            raw_data = profiles[ch]
            if raw_data is not None:
                num_shots = data['n_shots'][i_chan]
                if data['dataset_type'][i_chan] == 2:  # ANALOG
                    #signal_data, units = calculate_physical_magnitudes_analog(raw_data, num_shots, data['adc_range'][i_chan], data['adc_bits'][i_chan])
                    if 'f' in data['channel'][i_chan]:
                        #signal_data, units = raw_data/15.0, ''
                        signal_data, units = raw_data, ''
                    elif 'n' in data['channel'][i_chan]:
                        #signal_data, units = raw_data/30.0, ''
                        signal_data, units = raw_data, ''
                    else:
                        signal_data, units = raw_data, ''
                elif data['dataset_type'][i_chan] == 3:  # PHOTONCOUNTING
                    #signal_data, units = calculate_physical_magnitudes_photoncounting(raw_data, num_shots, LIDAR_INFO[lidar_system]['DEFAULT_RESOLUTION'], data['range_resol'])
                    if 'f' in data['channel'][i_chan]:
                        #signal_data, units = raw_data/15.0, ''
                        signal_data, units = raw_data, ''
                    elif 'n' in data['channel'][i_chan]:
                        #signal_data, units = raw_data/30.0, ''
                        signal_data, units = raw_data, ''
                    else:
                        signal_data, units = raw_data, ''
                else:
                    logger.critical("Data Type %s not SD-type. Exit" % data['dataset_type'][i_chan])
                    sys.exit(1)
                data['std_{:s}'.format(channels_name[i_chan])][index, :] = signal_data
                if index == 0:
                    data['units_std_{:s}'.format(channels_name[i_chan])] = units
    elif channels_type == 'pd':
        for i_chan, ch in enumerate(channels_id):
            if profiles[ch] is not None:
                ch_n = channels_name[i_chan]
                s_p = int(data['laser_power_{:s}'.format(ch_n)][index, :].shape[0])
                data['laser_power_{:s}'.format(ch_n)][index, :] = profiles[ch][:s_p]
                data['units_laser_power_{:s}'.format(ch_n)] = 'a.u.'
    else:
        logger.critical("Channel Type %s not recognized. Exit" % channels_type)
        sys.exit(1)

    # Times
    t_start = dt.datetime.strptime(header['datetime_start'], DATE_FMT)
    t_end = dt.datetime.strptime(header['datetime_end'], DATE_FMT)
    data['time'][index] = t_start
    logger.debug('datetime: %s', data['time'][index])
    data['time_resol'] = (t_end - t_start).total_seconds()

    # Channels
    data['n_chan_vector'][index] = header['num_datasets']

    logger.info("End set data for index=%i" % index)
    return data


def set_final_arrangements(lidar_system, data, data_dim, channels_type, conf, logger):
    """[summary]

    Args:
        data ([type]): [description]
        channel_type ([type]): [description]
        channels_to_read ([type]): [description]
        conf ([type]): [description]
        logger ([type]): [description]

    Returns:
        [type]: [description]
    """
    # MULHACEN: RENAME CHANNELS after given dates
    if lidar_system == 'MULHACEN':
        DATE_ROTATIONAL_RAMAN355 = '15/12/2016 00:00:00'
        DATE_ROTATIONAL_RAMAN532 = '04/05/2017 00:00:00'
        for ic, wv in enumerate(data['wavelength']):
            # Raman 355
            if '387' in data['channel'][ic]: 
                if data['time'][0] >= dt.datetime.strptime(DATE_ROTATIONAL_RAMAN355, DATE_FMT):
                    new_name = '354xtp'
                    old_name = data['channel'][ic]
                    #data['wavelength'][ic] = 353.9
                    data['wavelength'][ic] = 354
                    data['channel'][ic] = new_name
                    data['signal_%s' % new_name] = data['signal_%s' % old_name]
                    data['units_signal_%s' % new_name] = data['units_signal_%s' % old_name]
                    del data['signal_%s' % old_name], data['units_signal_%s' % old_name]
                    logger.info('Raman wavelength at 387 changed by %s ' % data['wavelength'][ic])
            # Raman 530
            if '607' in data['channel'][ic]:
                if data['time'][0] >= dt.datetime.strptime(DATE_ROTATIONAL_RAMAN532, DATE_FMT):            
                    new_name = '530xtp'
                    old_name = data['channel'][ic]
                    #data['wavelength'][ic] = 530.2
                    data['wavelength'][ic] = 530
                    data['channel'][ic] = new_name
                    data['signal_%s' % new_name] = data['signal_%s' % old_name]
                    data['units_signal_%s' % new_name] = data['units_signal_%s' % old_name]
                    del data['signal_%s' % old_name], data['units_signal_%s' % old_name]
                    logger.info('Raman wavelength at 607 changed by %s ' % data['wavelength'][ic])

    # Polarization as a number
    data['polarization'] = [POLARIZATION[val_] for val_ in data['polarization']]

    # Correct values of zenith, azimuth for mulhacen
    if lidar_system == 'MULHACEN':
        data['zenith'] = data['zenith'] + 90
        data['azimuth'] = data['azimuth'] - 1

    # Detection mode as expected
    for i, ch in enumerate(data['channel_id']):
        if 'BT' in ch or '2A' in ch:
            dm = DETECTION_MODES['analog']
        elif 'BC' in ch or '2P' in ch:
            dm = DETECTION_MODES['photoncounting']
        elif 'PD' in ch:
            dm = DETECTION_MODES['laser_power']
        else:
            continue
        data['detection_mode'][i] = dm

    # IF RCS: PR2 and background
    if channels_type == 'rs':
        data['range'] = np.arange(1, data_dim['range'] + 1) * data['range_resol']
        # min and max alt for background signal calculation
        bck_min_alt, bck_max_alt = get_bck_alt(lidar_system, conf, logger)
        # bacground altitude filter
        data['bckgrd_rcs_comment'] = BCK_COMMENT_FMT.format(bck_min_alt, bck_max_alt)
    elif channels_type == 'sd':
        data['range'] = np.arange(1, data_dim['range'] + 1) * data['range_resol']
    elif channels_type == 'pd':
        data['n_pd0'] = np.arange(1, data_dim['n_pd0'] + 1) * data['range_resol']
        data['n_pd1'] = np.arange(1, data_dim['n_pd1'] + 1) * data['range_resol']
        data['n_pd0_comment'] = "num of shots fixed to first binary file information in order to set length of dimension"
        data['n_pd1_comment'] = "num of shots fixed to first binary file information in order to set length of dimension"
    else:
        logger.critical("Channel Type %s not recognized. Exit" % channels_type)
        sys.exit(1)

    return data


def read_data(list_files, conf, logger):
    """ Read Binary Files and create dictionary to be converted into netcdf file by:
        ./tools/create_netcdf.py: create_netcdf

    Args:
        list_files ([type]): [description]
        conf ([type]): [description]
        logger ([type]): [description]
    """
    logger.info('Start Lidar Reader')

    # Get Lidar Config Info: name, channels
    # pdb.set_trace()
    lidar_config = get_lidar_config(conf, logger)
    # Break-down lidar_config
    lidar_system = lidar_config['lidar_system']
    config_channels_id = lidar_config['channels_id']
    config_channels_name = lidar_config['channels_name']
    channels_type = lidar_config['channels_type']

    logger.info("System: %s" % lidar_system)

    # Get Data Size. It also retrieves list of valid files
    data_dim, list_files = get_data_size(list_files, lidar_system, config_channels_id, channels_type, logger)

    # Loop over files
    data = {}
    for index, file_ in enumerate(list_files):
        # read header and profiles
        header, profiles = read_file(file_, config_channels_id, logger)
        # add file data
        data = set_data(lidar_system, data, index, header, profiles, data_dim, \
            channels_type, config_channels_id, config_channels_name, logger)
    data = set_final_arrangements(lidar_system, data, data_dim, channels_type, conf, logger)

    logger.info('End Lidar Reader')

    return data
