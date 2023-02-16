# -*- coding: utf-8 -*-
"""
Created on Wed Mar  2 15:01:22 2022

@author: user
"""

import pandas as pd 
import glob 
import os 
import logging
from datetime import datetime,timedelta 
import argparse
import pdb
import numpy as np

logger = logging.getLogger(__name__)
import shutil



def s_path(date):
    mainspath = 'C:\\Lidar_Data\\Scanning_Measurements'
    yyyy = date.strftime('%Y')
    mm = date.strftime('%m')
    dd  = date.strftime('%d')
    # print(os.path.join(mainspath,yyyy,mm,dd,'*S*')
    return os.path.join(mainspath,yyyy,mm,dd,'*S*')

def fp_path (date):
    mainspath = 'C:\\Lidar_Data\\Fixed_Point'
    ymd = date.strftime('%Y%m%d')
    return os.path.join(mainspath,ymd)

    

def dest_path(lidar_name,date):
    mainspath = 'Z:\\Lidar_Data'
    yyyy = date.strftime('%Y')
    mm = date.strftime('%m')
    dd  = date.strftime('%d')
    return os.path.join(mainspath,lidar_name.upper(),'0a',yyyy,mm,dd)


def create_folder(dn):
    """

    Input:
    dn: Directory Name Full path To Be created. String

    Output:
    result: Dir created or not. Bool
    """

    logger.info("Creating Directory %s..."%dn)
    # pistas para crear directorios: os.chmod, os.umask, os.mkdir
    assert isinstance(dn, str), "dn must be String Type"
    result = True
    if not os.path.isdir(dn):
        try:
            os.makedirs(dn, mode=0o777)
        except Exception as e:
            logger.warning(str(e))
            result = False

    if result:
        logger.info("Directory Created %s." % dn)
    else:
        logger.warning("Directory Not Created %s. Check Manually" % dn)

    return result
    
def copy_files_to_folder(fns, dn):
    """

    Input:
    fns: filenames full path. String/List
    dn: destiny directory full path. String

    Output:
    result: Copy successful or failed. Bool
    """
    
    # If only one file
    if isinstance(fns, str):
        fns = [fns]

    if len(fns) > 0:
        logger.info("Copying Files %s [...] %s to Directory: %s..."%(fns[0], fns[-1], dn))
        # Destiny Dir Exists
        copied_fns = []
        if os.path.isdir(dn):
            for fn in fns:
                try:
                    if os.path.isfile(fn):
                        shutil.copy(fn, dn)
                except Exception as e:
                    logger.warning(str(e))
                copied_fn = os.path.join(dn, os.path.basename(fn))
                if os.path.isfile(copied_fn):
                    copied_fns.append(copied_fn)
            # Check Copy
            if [os.path.basename(x) for x in fns] == [os.path.basename(x) for x in copied_fns]:
                result = True
            else:
                result = False
        else:
            result = False

        if result:
            logger.info("Files copied to %s." % dn)
        else:
            logger.warning("Files not copied to %s. Check Manually" % dn)
    else:
        return False

    return result    

def get_date_from_filename(fn):
    """
    Takes the date (YYYYMMDD_HHMM) from the measurement file name

    Input:
    fn: Filename (Full path or just the file). String

    Output:
    date_dt: Date in datetime.datetime
    date_str: Date in String format
    ymd_tuple: Tuple of Strings: yyyy, mm, dd
    """

    assert isinstance(fn, str), "m_type must be String Type"

    try:
        # Assure Only Filename
        fn = os.path.basename(fn)
        for i, x in enumerate(fn):
            cc = i
            if x.isnumeric():
                break
        if cc < len(fn) - 1:
            f00 = fn[cc:]
            yyyy = 2000 + int(f00[:2])
            mm = int(f00[2:3], 16)
            dd = int(f00[3:5])
            HH = int(f00[5:7])
            MM = int(f00[8:10])
            SS = int(f00[10:12])
            date_dt = datetime(yyyy,mm,dd,HH,MM,SS)
            date_str = date_dt.strftime("%Y%m%d_%H%M")
            ymd_tuple = "%04d"%yyyy,  "%02d"%mm, "%02d"%dd
        else:
            # NO HA ENCONTRADO NUMEROS. DEBE FALLAR
            date_dt = None
            date_str = None
            ymd_tuple = None
    except Exception as e:
        date_dt = None
        date_str = None
        ymd_tuple = None
        logger.warning(str(e))

    return date_dt, date_str, ymd_tuple
    


# INPUT arguments
def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def main():
    parser = argparse.ArgumentParser(description="usage %prog [arguments]")
    parser.add_argument("-m", "--measurement_type",
        action="store",
        dest="m_type",
        default=None,
        help="Measurement Type[example: RS, DP, HF, OT, TC")
    parser.add_argument("-c", "--clean_raw",
        type=str2bool,
        action="store",
        dest="clean_raw",
        default=False,
        help="Bool to Clean RAW directory[True, False]")
    parser.add_argument("-b", "--update_bkp",
        type=str2bool,
        action="store",
        dest="update_bkp",
        default=False,
        help="Bool to Update Backup space [True, False]")
    parser.add_argument("-l", "--lidar",        
        action="store",
        dest="lidar",
        default="mulhacen",
        help="Lidar system name [mulhacen, alhambra, veleta]")    
    parser.add_argument("-i", "--initial_date",
          action="store",
          dest="date_ini_str",
          # default='20180101',
          help="Initial date [example: '20190131'].")
    parser.add_argument("-e", "--final_date",
          action="store",
          dest="date_end_str", 
          required=False,
          help="Final date [example: '20190131'].")   
    
    args = parser.parse_args()   
    
    # pdb.set_trace()
    
    # print(args)
    # print(args.date_ini_str)
    # args 
    
    # date_ini = '20180101'
    # date_end = '20180123'
    if  np.logical_and (args.date_ini_str is None,args.date_end_str is None):
        args.date_ini_str =(datetime.now()-timedelta(days=1)).strftime('%Y%m%d')
        args.date_end_str = datetime.now().strftime('%Y%m%d')
    elif args.date_end_str is None:
        args.date_end_str = args.date_ini_str
        
    date_range = pd.date_range(args.date_ini_str, args.date_end_str)
   
    for i_date in date_range:
        # scanning 
        s_dn = s_path(i_date)
        sfn = glob.glob(s_dn)
        if len(sfn) > 0:
            for fn in sfn:
                dest_dn = os.path.join(dest_path(args.lidar,i_date),fn.split('\\')[-1])
                dest_dn_created = create_folder(dest_dn)
                fns = glob.glob(os.path.join(fn,'RM*'))
                copy_files_to_folder(fns,dest_dn)
        # Fixed point
        fp_dn = glob.glob(fp_path(i_date))
        if len(fp_dn)>0:
            for fpdn in fp_dn:
                fns = glob.glob(os.path.join(fpdn,'RM*'))
                if len(fns)>0:
                    date_first_file_dt, date_first_file, ymd_tuple  = get_date_from_filename(os.path.basename(fns[0]))
                    dest_rel_dn = "%s_%s" % ('FP', date_first_file)
                    dest_dn = os.path.join(dest_path(args.lidar,i_date),dest_rel_dn)
                    dest_dn_created = create_folder(dest_dn)
                    copy_files_to_folder(fns,dest_dn)
                    
                fnsdc = glob.glob(os.path.join(fpdn,'DC*'))
                if len(fnsdc) > 0:
                    for fndc in fnsdc:
                        fns = glob.glob(os.path.join(fndc,'RM*'))
                        if len(fns)>0:
                            date_first_file_dt, date_first_file, ymd_tuple  = get_date_from_filename(os.path.basename(fns[0]))
                            dest_rel_dn = "%s_%s" % ('DC', date_first_file)
                            dest_dn = os.path.join(dest_path(args.lidar,i_date),dest_rel_dn)
                            dest_dn_created = create_folder(dest_dn)
                            copy_files_to_folder(fns,dest_dn)
                # pdb.set_trace()
                fnsdp = glob.glob(os.path.join(fpdn,'DP*'))
                if len(fnsdp)>0:
                    # Sub-Measurements: deduced from folder names
                    for fndp in fnsdp:
                        sub_dns =  glob.glob(os.path.join(fndp, '*'))
                        if len(sub_dns)>0:
                            for sub_dn in sub_dns:
                                fnsfolder = glob.glob(os.path.join(sub_dns[0],'RM*'))
                                date_first_file_dt, date_first_file, ymd_tuple  = get_date_from_filename(os.path.basename(fnsfolder[0]))
                                dest_rel_dn = "%s_%s" % ('DP', date_first_file)
                                fns = glob.glob(os.path.join(sub_dn,'RM*'))
                                if len(fns)>0:
                                    dest_dn = os.path.join(dest_path(args.lidar,i_date),dest_rel_dn,os.path.basename(sub_dn))
                                    dest_dn_created = create_folder(dest_dn)
                                    # pdb.set_trace()
                                    copy_files_to_folder(fns,dest_dn)
                fnsdp = glob.glob(os.path.join(fpdn,'TC*'))
                if len(fnsdp)>0:
                    # Sub-Measurements: deduced from folder names
                    for fndp in fnsdp:
                        sub_dns =  glob.glob(os.path.join(fndp, '*'))
                        if len(sub_dns)>0:
                            for sub_dn in sub_dns:
                                fnsfolder = glob.glob(os.path.join(sub_dns[0],'RM*'))
                                date_first_file_dt, date_first_file, ymd_tuple  = get_date_from_filename(os.path.basename(fnsfolder[0]))
                                dest_rel_dn = "%s_%s" % ('TC', date_first_file)
                                fns = glob.glob(os.path.join(sub_dn,'RM*'))
                                if len(fns)>0:
                                    dest_dn = os.path.join(dest_path(args.lidar,i_date),dest_rel_dn,os.path.basename(sub_dn))
                                    dest_dn_created = create_folder(dest_dn)
                                    # pdb.set_trace()
                                    copy_files_to_folder(fns,dest_dn)
                # elif np.logical_or(glob.glob(os.path.join(fpdn,'TC*')),glob.glob(os.path.join(fpdn,'DP*'))):
                #     pass
                        
                        
    

if __name__== "__main__":
    main()
         