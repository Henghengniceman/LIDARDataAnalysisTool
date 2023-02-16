#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
User-defined reader for raw data from ALHAMBRA LIDAR
the file format is based on LICEL file format
"""
from __future__ import print_function, absolute_import, division
from configparser import RawConfigParser

import os
import sys
import ast
import datetime as dt
from collections import OrderedDict

import numpy as np
import netCDF4 as nc
import pdb

""" Constants for the module
"""
# brand and model of the LIDAR
BRAND = 'Raymetrics'
MODEL = 'ALHAMBRA'

DATETIME_FMT = '{} {}'
DATE_FMT = '%d/%m/%Y %H:%M:%S'
TIME_FMT = '%H:%M:%S'

N_HEADER_LINE = 3

MISSING_FLOAT = np.nan
MISSING_INT = -9

POLARIZATION = {
    'o': 0,
    'p': 1,
    's': 2
}

DEFAULT_RESOLUTION = 7.5

# Background Things
BCK_MIN_ALT = 50000
BCK_MAX_ALT = 60000
BCK_MIN_ALT_KEY = 'bckgrd_min_alt'  # field name in .ini [reader_conf]
BCK_MAX_ALT_KEY = 'bckgrd_max_alt'
BCK_COMMENT_FMT = 'calcultated between {:5d} m and {:5d} m'

# DEFAULT CHANNELS IN ALHAMBRA
CHANNELS = ['BT0', 'S2A0', 
            'BT1', 'S2A1', 
            'BT2', 'S2A2', 'BC2', 'S2P2', 
            'BT3', 'S2A3', 'BC3', 'S2P3',
            'BT4', 'S2A4', 'BC4', 'S2P4',
            'BT5', 'S2A5', 'BC5', 'S2P5',
            'BT6', 'S2A6', 'BC6', 'S2P6',
            'BT7', 'S2A7', 'BC7', 'S2P7',
            'BT10', 'S2A10',
            'BT11', 'S2A11', 'BC11', 'S2P11',
            'BT12', 'S2A12', 'BC12', 'S2P12',
            'BT13', 'S2A13', 'BC13', 'S2P13',
            'BT14', 'S2A14', 'BC14', 'S2P14',
            'BT15', 'S2A15', 'BC15', 'S2P15',
            'BT16', 'S2A16', 
            'PD00', 'PD01']
NUMBER_OF_CHANNELS = len(CHANNELS) # 54
CHANNEL_NUMBER = {}
for i in range(len(CHANNELS)):
   CHANNEL_NUMBER[CHANNELS[i]] = "%02d" % i


def date_to_dt(date_num, date_units):
    """ convert date np.array from datenum to datetime.datetime """

    return nc.num2date(date_num,
                       units=date_units,
                       calendar='standard')


""" Functions for reading conf_prod_ALHAMBRA*.ini """
def get_channel_number(conf, logger):
    """ Assign Number to Channel to Be Read as Configured in .ini

    Args:
        conf ([type]): [description]
        logger ([type]): [description]
    """

    # Parse Channels from Config ini
    try:
        tmp_chan = ast.literal_eval(conf['channels'])
    except ValueError:
        logger.critical("error parsing 'channels' option in [reader_conf] in config file. quitting")
        sys.exit(1)
    
    # If Channels in Config File OK:
    if all([cc in CHANNELS for cc in tmp_chan]):
        sub_channels_number = {c: CHANNEL_NUMBER[c] for c in tmp_chan}
    else:
        logger.critical("Wrong Channel Name in Config file. Exit")
        sys.exit(1)

    return sub_channels_number


def get_bck_alt(conf, logger):
    """get value of maximum and minimum altitude for background signal calculation
    if not define, use default value"""

    try:
        min_alt = ast.literal_eval(conf[BCK_MIN_ALT_KEY])
    except KeyError:
        min_alt = BCK_MIN_ALT
        logger.warning('%s not defined in conf file. Using default value %d',
                       BCK_MIN_ALT_KEY, BCK_MIN_ALT)
    except ValueError:
        logger.critical("error parsing '%s' option in [reader_conf] in config file. quitting",
                        BCK_MIN_ALT_KEY, conf[BCK_MIN_ALT_KEY])
        sys.exit(1)

    try:
        max_alt = ast.literal_eval(conf[BCK_MAX_ALT_KEY])
    except KeyError:
        max_alt = BCK_MAX_ALT
        logger.warning('%s not defined in conf file. Using default value %d',
                       BCK_MAX_ALT_KEY, BCK_MAX_ALT)
    except ValueError:
        logger.critical("error parsing '%s' option in [reader_conf] in config file. quitting",
                        BCK_MAX_ALT_KEY, conf[BCK_MAX_ALT_KEY])
        sys.exit(1)

    return min_alt, max_alt


def read_header(file_id, logger):
    """ Get Info from File Header (ASCII)

    Args:
        file_id ([type]): [description]
    """
    logger.debug('Start Reading Header')

    header = {}

    # point at beginning
    file_id.seek(0)

    # First Line is File Name
    logger.debug('First Line')
    line = file_id.readline()
    if isinstance(line, bytes):
        line = line.decode("utf-8")
    header['file_name'] = line.split()[0]

    # Second Line: spatio-temporal info
    logger.debug('Second Line')
    line = file_id.readline()
    if isinstance(line, bytes):
        line = line.decode("utf-8")
    elts = line.split()
    if len(elts) == 10:
        header['location'] = elts[0]
        header['datetime_start'] = DATETIME_FMT.format(elts[1], elts[2])
        header['datetime_end'] = DATETIME_FMT.format(elts[3], elts[4])
        header['altitude'] = float(elts[5])
        header['longitude'] = float(elts[6])
        header['latitude'] = float(elts[7])
        header['zenith'] = float(elts[8])
        header['azimuth'] = float(elts[9])
    else:
        logger.critical("Line 2 has different elements than expected (10). Exit")
        sys.exit(1)

    # Third Line: Laser, Dataset Info
    logger.debug('Third Line')
    line = file_id.readline()
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
    dataset_info = {}
    for i in range(header['num_datasets']):
        line = file_id.readline()
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
        channel_description['input_range_discriminator_level'] = float(elts[14])
        channel_description['channel_descriptor'] = elts[15]
        if len(elts) >= 18:
            channel_description['channel_name_licel'] = elts[16].replace('"', '')
            channel_description['channel_name'] = elts[17].replace('"', '')
        else:
            channel_description['channel_name_licel'] = ''
            channel_description['channel_name'] = ''
        dataset_info[i] = channel_description
    header['dataset_info'] = dataset_info

    logger.debug('End Reading Header')

    return header


def get_data_size(list_files, config, logger):
    """ Define Data Dimensions

    Args:
        list_files ([type]): [description]
        config ([type]): [description]
        logger ([type]): [description]
    """

    """ Initialize dimensions """
    data_dim = {}

    # time
    dim_time = len(list_files)
    # time ¿boundaries?: start/end of measurements within the file
    dim_nv = 2

    """ Get Channels Info (by Reading a Header File) """
    file_ref = list_files[0]
    if os.path.isfile(file_ref):
        try:
            with open(file_ref, 'rb') as fid:
                header = read_header(fid, logger)
        except IOError:
            logger.error("error trying to open " + file_ref)
    else:
        logger.error("File %s Not Found." % file_ref)
    channels_number = get_channel_number(config, logger) 
    channels_in_ini = [x for x in channels_number]
    channels_in_bin = [header['dataset_info'][x]['channel_descriptor'] \
        for x in header['dataset_info']]

    # We distinguish between (rcs, std) and (photodiode)
    channels_to_read = {}
    if all('PD' in c for c in channels_in_ini):  # PHD
        channel_type = 'laser_power'
        if 'PD00' in channels_in_bin:
            channels_to_read['PD00'] = channels_number['PD00']
            idx = channels_in_bin.index('PD00')
            data_dim['n_pd1'] = header['dataset_info'][idx]['num_bins']
            # for the shake of the health
            if data_dim['n_pd1'] > 600:
                data_dim['n_pd1'] = 600
        if 'PD01' in channels_in_bin:
            channels_to_read['PD01'] = channels_number['PD01']
            idx = channels_in_bin.index('PD01')
            data_dim['n_pd2'] = header['dataset_info'][idx]['num_bins']
            # for the shake of the health
            if data_dim['n_pd2'] > 1200:
                data_dim['n_pd2'] = 1200
        data_dim['n_chan'] = 2
    else:  # RCS, STD
        if 'B' in channels_in_ini[0]:
            channel_type = 'rcs'
        elif 'S' in channels_in_ini[0]:
            channel_type = 'std'
        else:
            logger.critical("Channel type Not Found. Exit")
        # channels
        dim_chan = 0
        ranges_list = []
        for ch in channels_in_ini:
            if ch in channels_in_bin:
                channels_to_read[ch] = channels_number[ch]
                idx = channels_in_bin.index(ch)
                ranges_list.append(header['dataset_info'][idx]['num_bins'])
                dim_chan += 1
            else:
                logger.warning("Channel %s not in Binary File" % ch)
        ranges_list = np.array(ranges_list)
        if not all(ranges_list - ranges_list[0] == 0):
            logger.critical("Num Bins Not All Equal among channels. Exit")
            sys.exit(1)
        dim_range = ranges_list[0]
    
        data_dim['n_chan'] = dim_chan
        data_dim['range'] = dim_range

    data_dim['time'] = dim_time
    data_dim['nv'] = dim_nv

    return data_dim, channel_type, channels_to_read


def read_profiles(fid, header, logger):
    """[summary]

    Args:
        fid ([type]): [description]
        header ([type]): [description]
        logger ([type]): [description]
    """

    # beginning of file
    fid.seek(0)

    # skip header (ASCII part of the file)
    num_datasets = header['num_datasets']
    lines_to_skip = N_HEADER_LINE + num_datasets + 1
    for i in range(lines_to_skip):
        fid.readline()

    # read profiles
    profiles = {}
    for i_chan in range(num_datasets):
        s_chan = header['dataset_info'][i_chan]['channel_descriptor'] 
        tmp_data = np.fromfile(fid, dtype='i4', count=\
            header['dataset_info'][i_chan]['num_bins'])
        profiles[s_chan] = tmp_data
        fid.seek(fid.tell()+2)

    # end of file?
    eor = fid.tell()
    eof = fid.seek(0, 2)
    if eor != eof:
        logger.critical("EOF not reached. Wrong read. Exit")
        sys.exit(1)

    return profiles


def read_data_file(file_fn, logger, channels=None):
    """[summary]

    Args:
        file_fn ([type]): [description]
        channels ([type]): [description]
        logger ([type]): [description]

    Returns:
        [type]: [description]
    """
    logger.info("reading %s", file_fn)
    try:
        fid = open(file_fn, 'rb')
    except IOError:
        logger.error("error trying to open " + file_fn)
        #continue
    header = read_header(fid, logger)
    profiles = read_profiles(fid, header, logger)
    fid.close()

    if channels is not None:
        new_dataset_info = {}
        new_profiles = {}
        i_ch = 0
        for ch in channels:
            new_profiles[ch] = profiles[ch]
            x = [header['dataset_info'][x]['channel_descriptor'] == ch \
                for x in header['dataset_info']]
            z = np.array([*header['dataset_info'].keys()])
            ch_n = int(z[x])
            new_dataset_info[i_ch] = header['dataset_info'][ch_n]
            i_ch += 1
        header['dataset_info'] = new_dataset_info
        header['num_datasets'] = len(channels)

        profiles = new_profiles

    return header, profiles


def set_data(data, index, header, profiles, data_dim, channel_type, \
    channels_to_read, logger):
    """[summary]

    Args:
        data ([type]): [description]
        index ([type]): [description]
        header ([type]): [description]
        profiles ([type]): [description]
        data_dim ([type]): [description]
        channel_type ([type]): [description]
        channels_to_read ([type]): [description]
        conf ([type]): [description]
        logger ([type]): [description]
    """

    logger.info("Start set data for index=%i" % index)

    # Size of Dimensions
    n_t = data_dim['time']
    n_v = data_dim['nv']
    if np.logical_or(channel_type == 'rcs', channel_type == 'std'):
        n_c = data_dim['n_chan']
        n_r = data_dim['range']
    elif channel_type == 'laser_power':
        n_c = 2
        n_r = 0
        n_pd1 = data_dim['n_pd1']
        n_pd2 = data_dim['n_pd2']
        laser_channel = {}
        for ch in channels_to_read:
            if ch == 'PD00':
                laser_number = 1
                n_pd = n_pd1
            elif ch == 'PD01':
                laser_number = 2
                n_pd = n_pd2
            else:
                logger.critical("Laser Channel %s Not Found. Exit" % ch)
                sys.exit(1)
            laser_channel[ch] = {}
            laser_channel[ch]['laser_number'] = laser_number
            laser_channel[ch]['dim_pd'] = n_pd
    else:
        logger.critical("Data Type %s not found. Exit" % channel_type)
        sys.exit(1)

    """ Initialize data: data = {}
    """
    if not data:
        logger.info("Initialize Data ...")
        logger.info("Type: %s" % channel_type)

        # Coordinates 
        data['time'] = np.empty((n_t,), dtype=np.dtype(dt.datetime))
        data['time_bounds'] = np.empty((n_t, n_v), dtype=np.dtype(dt.datetime))
        #data['n_chan'] = np.empty((n_c,), dtype=np.str('<U2'))
        data['n_chan'] = np.empty((n_c,), dtype=np.int)

        # SCALAR Variables supposed to be constant along files
        data['nv'] = MISSING_INT

        data['location'] = ''
        data['latitude'] = MISSING_FLOAT
        data['longitude'] = MISSING_FLOAT
        data['altitude'] = MISSING_FLOAT
        data['zenith'] = MISSING_FLOAT
        data['frequency'] = MISSING_FLOAT    
        data['time_resol'] = MISSING_FLOAT
        data['range_resol'] = MISSING_FLOAT
        data['custom_comment'] = MISSING_FLOAT

        # Variables Constant in time
        data['channel_id'] = np.empty((n_c,), dtype=np.str('<U10'))
        data['dataset_type'] = np.zeros((n_c,), dtype=np.int)
        data['laser_source'] = np.zeros((n_c,), dtype=np.int)
        data['detection_mode'] = [''] * n_c
        data['range_resol_vect'] = np.ones((n_c,), dtype=np.float32) * MISSING_FLOAT
        data['wavelength'] = np.ones((n_c,), dtype=np.float32) * MISSING_FLOAT
        data['powermeter'] = np.ones((n_c,), dtype=np.float32) * MISSING_FLOAT
        data['laser_polarization'] = np.ones((n_c,), dtype=np.int)* MISSING_INT
        data['polarization'] = np.array(['o'] * n_c, dtype=np.str)
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
        data['active'] = np.zeros((n_t, n_c), dtype=np.int)
        data['voltage'] = np.ones((n_t, n_c), dtype=np.int) * MISSING_FLOAT
        data['n_chan_vector'] = np.ones((n_t,), dtype=np.int) * MISSING_INT

        # Range dependent Variables: rcs, std, photodiode
        if channel_type == 'rcs':
            for ch in channels_to_read:
                data['rcs_{:s}'.format(channels_to_read[ch])] = np.ones((n_t, n_r,), dtype=np.float32) * MISSING_FLOAT
                data['bckgrd_rcs_{:s}'.format(channels_to_read[ch])] = np.ones((n_t,), dtype=np.float32) * MISSING_FLOAT
                data['units_rcs_{:s}'.format(channels_to_read[ch])] = ''
        elif channel_type == 'std':
            for ch in channels_to_read:
                data['std_{:s}'.format(channels_to_read[ch])] = np.ones((n_t, n_r,), dtype=np.float32) * MISSING_FLOAT
                data['units_std_{:s}'.format(channels_to_read[ch])] = ''
        elif channel_type == 'laser_power':
            for ch in channels_to_read:
                l_ch = laser_channel[ch]
                data['laser_power_{:s}'.format(channels_to_read[ch])] = \
                    np.ones((n_t, l_ch['dim_pd'],), dtype=np.float32) * MISSING_FLOAT
                data['units_laser_power_{:s}'.format(channels_to_read[ch])] = ''
                #data['laser_power_%s' % l_ch['laser_number']] = \
                #    np.ones((n_t, l_ch['dim_pd'],), dtype=np.float32) * MISSING_FLOAT
                #data['units_laser_power_%s' % l_ch['laser_number']] = 'a.u.'        
        else:
            pass
        logger.info('... Done')
    
    """ Write in Data
    """
    dataset_info = header['dataset_info']

    """ Set Variables Independent on Time """
    if index == 0:
        data['nv'] = n_v

        data['location'] = header['location']
        data['latitude'] = header['latitude']
        data['longitude'] = header['longitude']
        data['altitude'] = header['altitude']
        data['zenith'] = header['zenith'] 
        data['azimuth'] = header['azimuth'] 
        data["laser1_shots"] = header['laser_1_num_shots']
        data['laser1_frequency'] = header['laser_1_pulse_frequency']
        data["laser2_shots"] = header['laser_2_num_shots']
        data['laser2_frequency'] = header['laser_2_pulse_frequency']
    
    data['n_chan_vector'][index] = header['num_datasets'] 

    """ Variables Channel Dependent """
    for i_chan in range(n_c):
        data['active'][index, i_chan] = dataset_info[i_chan]['active']
        data['voltage'][index, i_chan] = dataset_info[i_chan]['pmt_voltage']
        if index == 0:
         
            # n_chan
            data['n_chan'][i_chan] = int(channels_to_read[dataset_info[i_chan]['channel_descriptor']])

            data['channel_id'][i_chan] = dataset_info[i_chan]['channel_name']
            data['dataset_type'][i_chan] = dataset_info[i_chan]['type']
            data['laser_source'][i_chan] = dataset_info[i_chan]['laser_source']
            data['telescope'][i_chan] = dataset_info[i_chan]['laser_source']
            data['n_range'][i_chan] = dataset_info[i_chan]['num_bins']
            data['laser_polarization'][i_chan] = dataset_info[i_chan]['laser_polarization']
            data['range_resol_vect'][i_chan] = dataset_info[i_chan]['bin_width']
            data['wavelength'][i_chan] = dataset_info[i_chan]['wavelength']
            data['polarization'][i_chan] = dataset_info[i_chan]['polarization']
            data['powermeter'][i_chan] = dataset_info[i_chan]['powermeter']

            data['n_shots'][i_chan] = dataset_info[i_chan]['num_shots']
            data['bin_shift'][i_chan] = dataset_info[i_chan]['bin_shift_int']
            data['bin_shift_dec'][i_chan] = dataset_info[i_chan]['bin_shift_dec']
            data['adc_bits'][i_chan] = dataset_info[i_chan]['ADC_bits']

            # detection mode: analog, photoncounting, laser_power
            if data['dataset_type'][i_chan] == 0 or data['dataset_type'][i_chan] == 2:  # Analog 
                data['detection_mode'][i_chan] = 'analog'
                data['adc_range'][i_chan] = dataset_info[i_chan]['input_range_discriminator_level']
            elif data['dataset_type'][i_chan] == 1 or data['dataset_type'][i_chan] == 3:  # Photoncounting
                data['detection_mode'][i_chan] = 'photoncounting'
                data['discriminator_level'][i_chan] = dataset_info[i_chan]['input_range_discriminator_level']
            elif data['dataset_type'][i_chan] == 4:  # Laser Power
                data['detection_mode'][i_chan] = 'laser_power'
                data['field_14'][i_chan] = dataset_info[i_chan]['input_range_discriminator_level']
            else:
                logger.critical("Data Type %s not recognized. Exit" % data['detection_mode'][i_chan])
                sys.exit(1)

    # Control Check: Range Resolution is the same:
    if len(np.unique(data['range_resol_vect'])) == 1:
        data['range_resol'] = data['range_resol_vect'][0]
    else:
        logger.critical("Range Resolution not the same in all profiles. Exit")
        sys.exit(1)
    
    # Assign Data Profiles
    if channel_type == 'rcs':
        # Build rcs variable
        for i_chan, ch in enumerate(channels_to_read):
            shots = data['n_shots'][i_chan]
            tmp_profile = profiles[ch] 
            if data['dataset_type'][i_chan] == 0:  # ANALOG
                max_range = data['adc_range'][i_chan]
                adc = data['adc_bits'][i_chan]
                scalefactor = ((max_range * 1000.) / shots )/ (2**adc - 1)
                # scalefactor = 1                
            elif data['dataset_type'][i_chan] == 1:  # PHOTONCOUNTING
                reduction_factor = DEFAULT_RESOLUTION / data['range_resol'] 
                scalefactor = (reduction_factor*20)/shots
                # scalefactor = 1
            else:
                logger.critical("Data Type %s not RCS-type. Exit" % data['dataset_type'][i])
                sys.exit(1)
            data['rcs_{:s}'.format(channels_to_read[ch])][index, :] = tmp_profile * scalefactor
    elif channel_type == 'std':
        for i_chan, ch in enumerate(channels_to_read):
            data['std_{:s}'.format(channels_to_read[ch])][index, :] = profiles[ch]
    elif channel_type == 'laser_power':
        for i_chan, ch in enumerate(channels_to_read):
            data['laser_power_{:s}'.format(channels_to_read[ch])][index, :] = profiles[ch][:laser_channel[ch]['dim_pd']]
    else:
        logger.critical("Channel Type %s not recognized. Exit" % channel_type)
        sys.exit(1)

    # Times
    data['time'][index] = dt.datetime.strptime(header['datetime_start'], DATE_FMT)
    logger.debug('datetime: %s', data['time'][index])
    data['time_bounds'][index, 0] = data['time'][index]
    data['time_bounds'][index, 1] = dt.datetime.strptime(header['datetime_end'], DATE_FMT)
    data['time_resol'] = (data['time_bounds'][index, 1] - data['time_bounds'][index, 0]).total_seconds()

    # Channels
    data['n_chan_vector'][index] = header['num_datasets']

    return data


def set_final_calculations(data, data_dim, channel_type, channels_to_read, conf, logger):
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
    # Polarization
    data['polarization'] = [POLARIZATION[val_] for val_ in data['polarization']]

    # IF RCS: PR2 and background
    if channel_type == 'rcs':
        data['range'] = np.arange(1, data_dim['range'] + 1) * data['range_resol']
        # min and max alt for background signal calculation
        bck_min_alt, bck_max_alt = get_bck_alt(conf, logger)
        # bacground altitude filter
        bck_filter = (data['range'] > bck_min_alt) & (data['range'] < bck_max_alt)
        data['bckgrd_rcs_comment'] = BCK_COMMENT_FMT.format(bck_min_alt, bck_max_alt)

        for i_chan, ch in enumerate(channels_to_read):
            # units
            if data['dataset_type'][i_chan] == 0:  # ANALOG
                tmp_units = 'mV'
            elif data['dataset_type'][i_chan] == 1:  # PHOTONCOUNTING
                tmp_units = 'MHz'
            else:
                logger.critical("Data Type %s not RCS-type. Exit" % data['dataset_type'][i])
                sys.exit(1)
            data['units_rcs_{:s}'.format(channels_to_read[ch])] = tmp_units

            # rcs, background
            tmp_profiles  = data['rcs_{:s}'.format(channels_to_read[ch])]
            square = np.square(data['range'])
            data['bckgrd_rcs_{:s}'.format(channels_to_read[ch])] = np.mean(tmp_profiles[:, bck_filter], axis=1)
            data['rcs_{:s}'.format(channels_to_read[ch])] = tmp_profiles * square
            data['units_rcs_{:s}'.format(channels_to_read[ch])] += '.m^2'

    elif channel_type == 'std':
        data['range'] = np.arange(1, data_dim['range'] + 1) * data['range_resol']
        for i_chan, ch in enumerate(channels_to_read):
            if data['dataset_type'][i_chan] == 2:  # ANALOG
                tmp_units = 'mV'
            elif data['dataset_type'][i_chan] == 3:  # PHOTONCOUNTING
                tmp_units = 'MHz'
            else:
                tmp_units = ''
            data['units_std_{:s}'.format(channels_to_read[ch])] = tmp_units

    elif channel_type == 'laser_power':
        data['n_pd1'] = np.arange(1, data_dim['n_pd1'] + 1) * data['range_resol']
        data['n_pd2'] = np.arange(1, data_dim['n_pd2'] + 1) * data['range_resol']
        data['n_pd1_comment'] = "num of shots fixed to first binary file information in order to set length of dimension"
        data['n_pd2_comment'] = "num of shots fixed to first binary file information in order to set length of dimension"
        for i_chan, ch in enumerate(channels_to_read):
            data['units_laser_power_{:s}'.format(channels_to_read[ch])] = 'a.u.'
    else:
        logger.critical("Channel Type %s not recognized. Exit" % channel_type)
        sys.exit(1)

    return data


def read_data(list_files, conf, logger):
    """[summary]

    Args:
        list_files ([type]): [description]
        conf ([type]): [description]
        logger ([type]): [description]
    """
    logger.info('Start reading of data using reader for %s %s', BRAND, MODEL)

    # Get Data Size
    data_dim, channel_type, channels_to_read = get_data_size(list_files, conf, logger)

    # Loop over files
    for ind, file_ in enumerate(list_files):
        # read header and profiles
        header, profiles = read_data_file(file_, logger, channels=channels_to_read.keys())
        # ind = 0: define data
        if ind == 0:
            data = {}
        # add to data
        data = set_data(data, ind, header, profiles, data_dim, channel_type, \
            channels_to_read, logger)

    data = set_final_calculations(data, data_dim, channel_type, channels_to_read, conf, logger)

    logger.info('End reading of data using reader for %s %s', BRAND, MODEL)
    return data