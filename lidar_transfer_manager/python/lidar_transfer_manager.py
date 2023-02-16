import os
import sys
import glob
import shutil
import argparse
import logging
import numpy as np
import pandas as pd
import datetime as dt
import pdb
logger = logging.getLogger(__name__)

__author__ = "Bermejo-Pantaleon, Diego"
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "GFAT"
__email__ = "dbp@ugr.es"
__status__ = "Development"

"""
Maquina: Solo para hacer tests
"""
#machine = "mac"
#machine = "test"
#machine = "mulhacen"

"""
Directories
"""
def paths(lidar='mulhacen'):
    if lidar == "mulhacen":
        work_dn = ""
        # RAW main directory
        raw_dn = os.path.join(work_dn, r"c:\Lidar_Data\RAWS")

        # BACKUP main directory
        bkp_dn = os.path.join(work_dn, r"g:\bkp")

        # NAS main directory
        nas_dn = os.path.join(work_dn, r"y:\datos\MULHACEN\0a")

        # CLEAN temporary directory
        cln_dn = os.path.join(work_dn, r"c:\Lidar_Data\Clean_Raw")

        # LOG directory
        log_dn = os.path.join(work_dn, r"c:\Lidar_Data\log")

    elif lidar == "alhambra":
        work_dn = ""
        # RAW main directory
        raw_dn = os.path.join(work_dn, r"c:\Lidar_Data\RAWS")

        # BACKUP main directory
        bkp_dn = os.path.join(work_dn, r"c:\Lidar_Data\bkp")

        # NAS main directory
        nas_dn = os.path.join(work_dn, r"y:\datos\ALHAMBRA\0a")

        # CLEAN temporary directory
        cln_dn = os.path.join(work_dn, r"c:\Lidar_Data\Clean_Raw")

        # LOG directory
        log_dn = os.path.join(work_dn, r"c:\Lidar_Data\log")

    elif lidar == "veleta":
        work_dn = ""
        # RAW main directory
        raw_dn = os.path.join(work_dn, r"C:\Lidar_Data\RAWS")

        # BACKUP main directory
        bkp_dn = os.path.join(work_dn, r"c:\Lidar_Data\bkp")

        # NAS main directory
        nas_dn = os.path.join(work_dn, r"c:\datos\KASCAL\0a")

        # CLEAN temporary directory
        cln_dn = os.path.join(work_dn, r"c:\Lidar_Data\Clean_Raw")

        # LOG directory
        log_dn = os.path.join(work_dn, r"c:\Lidar_Data\log")
    elif lidar == "kascal":
        work_dn = ""
        # RAW main directory
        raw_dn = os.path.join(work_dn, r"c:\Lidar_Data\RAW")
        
        # BACKUP main directory
        bkp_dn = os.path.join(work_dn, r"c:\Lidar_Data\bkp")

        # NAS main directory
        nas_dn = os.path.join(work_dn, r"z:\Lidar_Data\KASCAL\0a")

        # CLEAN temporary directory
        cln_dn = os.path.join(work_dn, r"c:\Lidar_Data\Clean_Raw")

        # LOG directory
        log_dn = os.path.join(work_dn, r"c:\Lidar_Data\log")

    elif lidar == "test":
        work_dn = ""
        # RAW main directory
        raw_dn = os.path.join(work_dn, r"c:\Lidar_Data\raw")

        # BACKUP main directory
        bkp_dn = os.path.join(work_dn, r"g:\bkp")

        # NAS main directory
        nas_dn = os.path.join(work_dn, r"y:\datos\test_dbp\nas")

        # CLEAN temporary directory
        cln_dn = os.path.join(work_dn, r"c:\Lidar_Data\cln")

        # LOG directory
        log_dn = os.path.join(work_dn, r"c:\Lidar_Data\log_test")

    elif lidar == "mac":
        work_dn = "/Volumes/HDD/share/OneDrive/Synchro/trabajo/iista/work/mulhacen_to_nas"
        # RAW main directory
        raw_dn = os.path.join(work_dn, "raw")

        # BACKUP main directory
        bkp_dn = os.path.join(work_dn, "bkp")

        # NAS main directory
        nas_dn = os.path.join(work_dn, "nas")

        # CLEAN temporary directory
        cln_dn = os.path.join(work_dn, "cln")

        # LOG directory
        log_dn = os.path.join(work_dn, "log")  
    else:
       raw_dn, bkp_dn, nas_dn, cln_dn, log_dn = None, None, None, None, None  
    return raw_dn, bkp_dn, nas_dn, cln_dn, log_dn

"""
Global
"""
# Types of Measurements
m_types_ls = ["RS", "DP", "TC", "HF", "OT",'ZS','AS','FP']


def date_for_log():
    """

    Output:
    Date string of current computer clock
    """
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def get_letter_code(m_type):
    """
    Get Id Letter to identify specific measurement files

    Input:
    m_type: Type of measurement. String

    Output:
    i_letter: Letter that identifies type of measurement in measurement files. String
    """

    assert isinstance(m_type, str), "m_type must be String Type"

    if m_type == "RS":
        i_letter = "R"
    elif m_type == "DP":
        i_letter = "R"
    elif m_type == "HF":
        i_letter = "R"
    elif m_type == "OT":
        i_letter = "R"
    elif m_type == "TC":
        i_letter = "R"
    elif m_type == "ZS":
        i_letter = "R"
    elif m_type == "AS":
        i_letter = "R"
    elif m_type == "FP":
        i_letter = "R"
        
    else:
        i_letter = None
        logger.error("%s is not a valid measurement type." % m_type)

    return i_letter


def search_measurement_files(dn, letter_id):
    """
    Search for measurement files in a directory using a letter id

    Input:
    dn: Directory with measurements. String
    letter_id: Letter ID for type of measurement file

    Output:
    fns: Measurement files. List of Strings
    """
    fns = []
    try:
        for root, dirs, files in os.walk(dn):
            for name in files:
                fns.append(os.path.join(root, name)) if letter_id in name else 0

    except Exception as e:
        logger.warning("Error searching measurement files in %s" % dn)

    return fns


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
            date_dt = dt.datetime(yyyy,mm,dd,HH,MM,SS)
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


def delete_folder(dn):
    """

    Input:
    dn: Directory Name Full path To Be Deleted. String

    Output:
    result: Dir deleted or not. Bool
    """

    logger.info("Deleting Directory %s..."%dn)
    assert isinstance(dn, str), "dn must be String Type"
    result = True
    if os.path.isdir(dn):
        try:
            shutil.rmtree(dn)
        except Exception as e:
            logger.warning(str(e))
            result = False

    if result:
        logger.info("Directory Deleted %s." % dn)
    else:
        logger.warning("Directory Not Deleted %s. Check Manually" % dn)

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
def copy_files_to_folder_FP(fns, dn):
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
            dayfile_new = ''
            date_file_new = '' 
            for fn in fns:
                try:
                    if os.path.isfile(fn):
                        m_fn_bn = os.path.basename(fn)
                        m_type = fn.split('\\')[-2]

                        _, date_file, ymd_tuple = get_date_from_filename(m_fn_bn)
                        # pdb.set_trace()
                        day_file = date_file.split('_')[0]
                        
                        if dayfile_new != day_file:
                            
                            dayfile_new = day_file
                            
                            date_file_new = date_file
                            dest_rel_dn = "%s_%s" % (m_type, date_file_new)
                            nas_dest_abs_dn = os.path.join(dn, *ymd_tuple, dest_rel_dn)                    
                            # bkp_dest_abs_dn = os.path.join(bkp_dn, *ymd_tuple, dest_rel_dn)
                            nas_dn_created = create_folder(nas_dest_abs_dn)
                    
                        
                        
                        # # Name of Measurement Folder in Destiny (Relative)
                        
                        
                        # # dest_rel_dn_new = ''
                        
                        # # if  dest_rel_dn_new != dest_rel_dn:
                        # #     dest_rel_dn_new = dest_rel_dn
                        # # Create Destiny Folder
                       
                        # nas_dest_abs_dn = os.path.join(dn, *ymd_tuple, dest_rel_dn)                    
                        # # bkp_dest_abs_dn = os.path.join(bkp_dn, *ymd_tuple, dest_rel_dn)
                        # nas_dn_created = create_folder(nas_dest_abs_dn)
                        
                        # pdb.set_trace()

                        # Non-measurement Files
                        # txt_fns = search_measurement_files(m_dn, ".txt")
                        # copy_files_to_folder(txt_fns, nas_dest_abs_dn)
                        # dat_fns = search_measurement_files(m_dn, ".dat")
                        # copy_files_to_folder(dat_fns, nas_dest_abs_dn)
                        shutil.copy(fn, nas_dest_abs_dn)
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


def copy_folder_contents(src, dst):
    """

    Input:
    src: Origin Folder. String.
    dst: Destiny Folder. String
    """
    result = True
    try:
        copied_all = []
        for root, dirs, files in os.walk(src):
            for fn in files:
                full_fn = os.path.join(root, fn)
                dn = os.path.dirname(full_fn)
                d_dn = os.path.join(dst, os.path.basename(dn))
                if not os.path.isdir(d_dn):
                    if not create_folder(d_dn):
                        copied = False
                copied = copy_files_to_folder(full_fn, d_dn)
                copied_all.append(copied)
        if all(copied_all):
            result = True
        else:
            result = False
    except Exception as e:
        logger.warning("Error in Copy Folder Contents. %s" % str(e))
        result = False

    return result


def transfer_measurement(m_type, delete_lag=5, update_bkp=False, lidar="mulhacen"):
    """
    Transfer a group of measurements of a given kind to NAS

    Input:
    m_type: Type of measurement. String
    delete_lag: Time Lag (in minutes) to determine if the measurement is considered finished to be removed from RAW. Integer
    update_bkp: Option to Update Space in BKP directory. Bool.

    """
    raw_dn, bkp_dn, nas_dn, _, _ = paths(lidar)
    # raw_dn = raw_dn
    logger.info("[%s] Start Transfer. %s" % (date_for_log(), m_type))
    assert isinstance(m_type, str), "m_type must be String Type"
    if m_type in m_types_ls:
        #i_letter
        i_letter = get_letter_code(m_type)
        # files pattern
        files_pattern = "%s*" % i_letter
        # pdb.set_trace()
        # Folder(s) with measurements
        m_dns = glob.glob(os.path.join(raw_dn, "%s*" % m_type))
        if len(m_dns) > 0:
            # Loop over Measurement Folders
            m_dns.sort()
            for m_dn in m_dns:
                # Name of measurement folder
                m_dn_bn = os.path.basename(m_dn)

                # order of measurement. Useful for searching DC associated measurements
                m_order = os.path.basename(m_dn).split(m_type)
                if len(m_order) > 1:
                    m_order = m_order[1]
                else:
                    m_order = ''

                # Search for Measurement Files
                m_fns = search_measurement_files(m_dn, i_letter)
                if len(m_fns) > 0:
                    # times of first, last measurements
                    m_fns_bn = [os.path.basename(x) for x in m_fns]
                    m_fns_bn.sort()
                    date_first_file_dt, date_first_file, _  = get_date_from_filename(m_fns_bn[0])
                    date_last_file_dt, date_last_file, _ = get_date_from_filename(m_fns_bn[-1])
                    _, _, ymd_tuple = get_date_from_filename(m_fns_bn[-1])

                    # Name of Measurement Folder in Destiny (Relative)
                    dest_rel_dn = "%s_%s" % (m_type, date_first_file)

                    # Create Destiny Folder
                    if m_type in ['ZS','AS']:
                        nas_dest_abs_dn = os.path.join(nas_dn, *ymd_tuple, m_dn_bn) 
                        bkp_dest_abs_dn = os.path.join(bkp_dn, *ymd_tuple, m_dn_bn)
                    else:    
                        nas_dest_abs_dn = os.path.join(nas_dn, *ymd_tuple, dest_rel_dn)                    
                        bkp_dest_abs_dn = os.path.join(bkp_dn, *ymd_tuple, dest_rel_dn)
                    nas_dn_created = create_folder(nas_dest_abs_dn)
                    bkp_dn_created = create_folder(bkp_dest_abs_dn)
                    
                    # pdb.set_trace()

                    # Non-measurement Files
                    txt_fns = search_measurement_files(m_dn, ".txt")
                    copy_files_to_folder(txt_fns, nas_dest_abs_dn)
                    dat_fns = search_measurement_files(m_dn, ".dat")
                    copy_files_to_folder(dat_fns, nas_dest_abs_dn)
                    
                    # pdb.set_trace()

                    # Manage Transfer Measurement Files to Destiny Folders according to Type of Measurement
                    if np.logical_or.reduce((m_type == "HF", m_type == "OT",m_type == "AS", m_type == "ZS")):
                        copy_to_nas_m = copy_files_to_folder(m_fns, nas_dest_abs_dn)
                        copy_to_bkp_m = copy_files_to_folder(m_fns, bkp_dest_abs_dn)
                    
                    elif np.logical_or(m_type == "RS", m_type == "FP"):
                        copy_to_nas_m = copy_files_to_folder_FP(m_fns,nas_dn)
                        copy_to_bkp_m = copy_files_to_folder_FP(m_fns,bkp_dn)

                    elif np.logical_or(m_type == "DP", m_type == "TC"):
                        # Sub-Measurements: deduced from folder names
                        sub_dns_bn = [os.path.basename(x) for x in glob.glob(os.path.join(m_dn, '*'))]
                        # Loop over DP types
                        copy_to_nas_sub, copy_to_bkp_sub = [], []
                        for sub_dn_bn in sub_dns_bn:
                            # Measurements
                            sub_m_fns = search_measurement_files(os.path.join(m_dn, sub_dn_bn), i_letter)
                            # Transfer
                            nas_sub_dn = os.path.join(nas_dest_abs_dn, sub_dn_bn)
                            bkp_sub_dn = os.path.join(bkp_dest_abs_dn, sub_dn_bn)
                            nas_sub_dn_created = create_folder(nas_sub_dn)
                            bkp_sub_dn_created = create_folder(bkp_sub_dn)
                            copy_to_nas_sub.append(copy_files_to_folder(sub_m_fns, nas_sub_dn))
                            copy_to_bkp_sub.append(copy_files_to_folder(sub_m_fns, bkp_sub_dn))
                        copy_to_nas_m = True if all(copy_to_nas_sub) else False
                        copy_to_bkp_m = True if all(copy_to_bkp_sub) else False
                    else:
                        logger.warning("Automatic Transfer for %s not implemented. Check Manually" % m_type)
                        copy_to_nas_m = False
                        copy_to_bkp_m = False

                    # Find Associated DC
                    dc_dns = glob.glob(os.path.join(raw_dn, "DC*"))
                    if len(dc_dns) > 0:  # Exist DC
                        dc_dns.sort()
                        dc_dns_bn = [os.path.basename(x) for x in dc_dns]
                        dc_flag = "DC%s" % m_order
                        if dc_flag in dc_dns_bn:  # Exist DC in order with M_TYPE
                            dc_dn = dc_dns[dc_dns_bn.index(dc_flag)]
                        else:  # Not Exist DC in order with M_TYPE
                            # Take the nearest DC
                            closeness = []
                            for dc_dn in dc_dns:
                                dc_fns = search_measurement_files(dc_dn, "R")
                                dc_fns_bn = [os.path.basename(x) for x in dc_fns]
                                dc_fns_bn.sort()
                                dc_first, _, _ = get_date_from_filename(dc_fns_bn[0])
                                dc_last, _, _ = get_date_from_filename(dc_fns_bn[-1])
                                closeness.append(np.min([abs(dc_last - date_first_file_dt), abs(dc_first - date_last_file_dt)]))
                            nearest = np.argmin(closeness)
                            dc_dn = dc_dns[nearest]
                        # Finally, DC measurements
                        dc_fns = search_measurement_files(dc_dn, "R")
                        # Name of Measurement Folder in Destiny (Relative)
                        dest_rel_dc_dn = "%s_%s" % ("DC", date_first_file)
                        # Create Destiny Folder for DC
                        nas_dest_abs_dc_dn = os.path.join(nas_dn, *ymd_tuple, dest_rel_dc_dn)
                        bkp_dest_abs_dc_dn = os.path.join(bkp_dn, *ymd_tuple, dest_rel_dc_dn)
                        nas_dc_dn_created = create_folder(nas_dest_abs_dc_dn)
                        bkp_dc_dn_created = create_folder(bkp_dest_abs_dc_dn)
                        # Transfer DC Measurement Files to Destiny Folders
                        copy_to_nas_dc = copy_files_to_folder(dc_fns, nas_dest_abs_dc_dn)
                        copy_to_bkp_dc = copy_files_to_folder(dc_fns, bkp_dest_abs_dc_dn)
                    else:
                        logger.warning("No DC found associated to %s. Check" % m_dn_bn)
                        copy_to_nas_dc = False
                        copy_to_bkp_dc = False

                    # Delete Folders: Measurements and DC
                    if np.logical_and(copy_to_nas_m, copy_to_bkp_m):  # Measurements can be potentially deleted
                        current_time = dt.datetime.now()
                        # If DC exists
                        if len(dc_dns) > 0:  # Exist dc_dn, dc_fns
                            # Take the date of latest file (either Meas. or DC) to check ability to delete
                            dc_fns_bn = [os.path.basename(x) for x in dc_fns]
                            date_last_file_dc_dt, date_last_file_dc, _ = get_date_from_filename(dc_fns_bn[-1])
                            date_last_file_x_dt = date_last_file_dt if date_last_file_dt > date_last_file_dc_dt else date_last_file_dc_dt
                            # Delete Meas. and DC if last file was created more than delete_lag ago
                            if (current_time - date_last_file_x_dt) > dt.timedelta(minutes=delete_lag):
                                logger.info("Measurement %s Finsihed. Proceed to Delete" % m_dn_bn)
                                m_dn_deleted = delete_folder(m_dn)
                                if np.logical_and(copy_to_nas_dc, copy_to_bkp_dc):
                                    logger.info("DC %s Finsihed. Proceed to Delete" % m_dn_bn)
                                    dc_dn_deleted = delete_folder(dc_dn)
                                else:
                                    logger.warning("DC %s Finished but not copied to NAS and BKP. Check." % m_dn_bn)
                            else:
                                logger.info("Measurement %s Still Active" % m_dn_bn)
                        else:  # If DC does not exist, keep measurement, if finished, until 00:00 of next day
                            if (current_time - date_last_file_dt) > dt.timedelta(minutes=delete_lag):  # Ability to delete
                                if current_time.day > date_last_file_dt.day:  # If Day of current_time has changed, then delete Measurement
                                    logger.info("Measurement %s Finsihed. Proceed to Delete" % m_dn_bn)
                                    m_dn_deleted = delete_folder(m_dn)
                else:
                    logger.warning("Files for %s not found. Check Manually" % m_type)
        else:
            logger.info("No %s Measurements Found." % m_type)
    else:
        logger.warning("%s is not a valid measurement type." % m_type)

    logger.info("[%s] End Transfer. %s" % (date_for_log(), m_type))

    # Update BKP available space
    if update_bkp:
        update_bkp_space()


def compare_nas_vs_bkp(nas_dn=None, bkp_dn=None):
    """
    Comparison File to File.
    1. Existence
    2. Size of files

    Input:
    nas_dn: NAS directory. String
    bkp_dn: BKP directory. String

    Output:
    result: Comparison Succesfull (True) or not (False). Bool
    """
    result = True
    if np.logical_and(nas_dn is not None, bkp_dn is not None):
        nas_fns = [os.path.join(root, x) for root, dirs, files in os.walk(nas_dn) for x in files]
        bkp_fns = [os.path.join(root, x) for root, dirs, files in os.walk(bkp_dn) for x in files]
        check_cp = []
        for nas_fn in nas_fns:
            # Existence
            exist_copy = [x for x in bkp_fns if nas_fn.replace(nas_dn, '') in x.replace(bkp_dn, '') ]
            if len(exist_copy) == 1:
                bkp_fn = exist_copy[0]
                # Sizes
                bkp_fn_sz = os.stat(bkp_fn).st_size
                nas_fn_sz = os.stat(nas_fn).st_size
                if nas_fn_sz < bkp_fn_sz:
                    try:
                        shutil.copyfile(bkp_fn, nas_fn)
                        check_cp.append(True)
                    except Exception as e:
                        logger.warning(str(e))
                        check_cp.append(False)
                elif nas_fn_sz > bkp_fn_sz:
                    try:
                        shutil.copyfile(nas_fn, bkp_fn)
                        check_cp.append(True)
                    except Exception as e:
                        logger.warning(str(e))
                        check_cp.append(False)
            else:
                check_cp.append(False)
        if all(check_cp):
            result = True
        else:
            result = False
    else:
        logger.warning("Error in Compare BKP vs NAS. NAS or BKP are None")
        result = False

    return result


def update_bkp_space(lidar='mulhacen'):
    """
    Check NAS and BKP synchro for a period of last 100 days
    BKP will keep 30 days of measurements
    """
    _, bkp_dn, nas_dn, _, _ = paths(lidar)

    logger.info("[%s] Start Update Backup." % date_for_log())
    # what's in the bkp
    today = dt.datetime.now()
    bkp_limit_date = today - dt.timedelta(days=30)
    date_range = pd.date_range(today - dt.timedelta(days=100), today - dt.timedelta(days=1))
    for i_date in date_range:
        i_date_str = i_date.strftime("%Y%m%d")
        # print(i_date_str)
        # NAS, BKP directories
        date_rel_path = os.path.join(*[i_date.strftime(x) for x in ["%Y", "%m", "%d"]])
        nas_date_dn = os.path.join(nas_dn, date_rel_path)
        bkp_date_dn = os.path.join(bkp_dn, date_rel_path)
        # Existence
        e_nas = os.path.isdir(nas_date_dn)
        e_bkp = os.path.isdir(bkp_date_dn)
        # Actions
        if not np.logical_and(e_nas, e_bkp):  # If any of (NAS, BKP) does not exist
            if np.logical_and(e_nas, not e_bkp):  # NAS exist, BKP does not exist
                logger.info("NAS dir exists. BKP dir does not exist.")
                # If i_date is closer within 1 month, NAS is copied to BKP
                if (i_date - bkp_limit_date) >= dt.timedelta(days=0):
                    if create_folder(bkp_date_dn):  # create folder
                        if not copy_folder_contents(nas_date_dn, bkp_date_dn):  # copy folder contents
                            logger.warning("Error in Copy %s From NAS to BKP. Check Manually" % i_date_str)
            elif np.logical_and(not e_nas, e_bkp):  # BKP exist, NAS does not exist
                logger.warning("BKP dir exists. NAS dir does not exist. Copy From BKP to NAS.")
                if create_folder(nas_date_dn):  # create folder
                    if not copy_folder_contents(bkp_date_dn, nas_date_dn):  # copy folder contents
                        logger.warning("Error in Copy %s From BKP to NAS. Check Manually" % i_date_str)
                else:
                    logger.warning("Error in Copy %s From BKP to NAS. Check Manually" % i_date_str)
            else:
                logger.info("No NAS nor BKP dir for %s. Check Manually" % i_date_str)

        # Compare NAS vs BKP if both exist
        if np.logical_and(e_nas, e_bkp):  # If Both (NAS, BKP) exists
            logger.info("Compare NAS and BKP dirs for %s." % i_date_str)
            result = compare_nas_vs_bkp(nas_dn=nas_date_dn, bkp_dn=bkp_date_dn)

        # Delete BKP if i_date is older than bkp_limit_date
        if (i_date - bkp_limit_date) < dt.timedelta(days=0):
            bkp_deleted = delete_folder(bkp_date_dn)

    # Delete BKP for months, years
    for i_date in date_range:
        month_rel_path = os.path.join(*[i_date.strftime(x) for x in ["%Y", "%m"]])
        bkp_month_dn = os.path.join(bkp_dn, month_rel_path)
        if os.path.isdir(bkp_month_dn):
            if len(os.listdir(bkp_month_dn)) == 0:
                bkp_deleted = delete_folder(bkp_month_dn)
        year_rel_path = os.path.join(*[i_date.strftime(x) for x in ["%Y"]])
        bkp_year_dn = os.path.join(bkp_dn, year_rel_path)
        if os.path.isdir(bkp_year_dn):
            if len(os.listdir(bkp_year_dn)) == 0:
                bkp_deleted = delete_folder(bkp_year_dn)
    logger.info("[%s] End Update Backup." % date_for_log())


def clean_raw_directory(lidar='mulhacen'):
    """
    Function to Clean Raw Directory of ALL measurements.
    Measurements folders in RAW directory are moved to a tmp directory for the manual management
    of RAW measurements
    """

    raw_dn, _, _, cln_dn, _ = paths(lidar)

    logger.info("[%s] Start Clean %s" % (date_for_log(), raw_dn))

    try:
        # First, create a Main Clean Directory if necessary:
        main_clean_dn_created = create_folder(cln_dn)
        if main_clean_dn_created:
            # Then, for the time this function is invoked, a clean sub-folder is created
            clean_date = date_for_log()
            clean_dn = os.path.join(cln_dn, "clean_%s" % clean_date)
            clean_dn_created = create_folder(clean_dn)
            if clean_dn_created:
                # List of Elements in RAW (folders, files). And MOVE them to CLEAN dir.
                lista = os.listdir(raw_dn)
                for elem in lista:
                    try:
                        shutil.move(os.path.join(raw_dn, elem), clean_dn)
                    except Exception as e:
                        logger.warning("Error moving folder %s to %s. Check" % (elem, clean_dn))
                lista_dest = os.listdir(clean_dn)
                if lista_dest == lista:
                    logger.info("Raw directory succesfully cleaned")
                else:
                    logger.info("Raw directory NOT succesfully cleaned. Check")
            else:
                logger.warning("Clean Directory %s not created. Clean Manually" % clean_dn)
        else:
            logger.warning("Main Clean Directory %s not created" % cln_dn)

    except Exception as e:
        logger.warning("Cleaning Raw Directory not performed")

    logger.info("[%s] End Clean. %s" % (date_for_log(), raw_dn))


def run(m_type=None, clean_raw=False, update_bkp=False, lidar="kascal"):
    """
    RUN management process to transfer Mulhacen Lidar measurements from PC to NAS and Backup

    Input:
    m_type: Type of measurement. String
    clean_raw: Option to Clean the RAW directory. Bool
    update_bkp: Option to Update Space in BKP directory. Bool

    """

    raw_dn, _, _, _, _ = paths(lidar)
    # pdb.set_trace()

    
    if not clean_raw:  # Operational Transfer
        # IF type not given, it is deduced
        if m_type is None:
            m_types = []
            for it in m_types_ls:  
                if it in ['AS','ZS']:
                    Raw_generate = raw_dn[:-4]
                    if len(glob.glob(os.path.join(Raw_generate,'RAW','Z*'))) == 0:
                        for year in os.listdir(os.path.join(Raw_generate,'Scanning_Measurements')):
                            for month in os.listdir(os.path.join(Raw_generate,'Scanning_Measurements',year)):
                                if month.startswith(tuple('0123456789')):
                                    for day in os.listdir(os.path.join(Raw_generate,'Scanning_Measurements',year,month)):
                                        if day.startswith(tuple('0123456789')):
                                            for time in os.listdir(os.path.join(Raw_generate,'Scanning_Measurements',year,month,day)):
                                                if time.endswith(tuple('0123456789')):
                                                    for file in os.listdir(os.path.join(Raw_generate,'Scanning_Measurements',year,month, day,time)):
                                                        if not os.path.exists(os.path.join(Raw_generate,'RAW',time)):
                                                                os.makedirs(os.path.join(Raw_generate,'RAW',time))  
                                                        shutil.copy(os.path.join(Raw_generate,'Scanning_Measurements',year,month, day,time,file),os.path.join(Raw_generate,'RAW',time))
                                            # pass
                # if it == 'FP':
                #     Raw_generate = raw_dn[:-4]
                #     if len(glob.glob(os.path.join(Raw_generate,'RAW','F*'))) == 0:
                #         if not os.path.exists(os.path.join(Raw_generate,'RAW',it)):
                #                 os.makedirs(os.path.join(Raw_generate,'RAW',it))
                #         for day in os.listdir(os.path.join(Raw_generate,'Fixed_Point')):
                #             if day.startswith(tuple('0123456789')):
                #                 for file in os.listdir(os.path.join(Raw_generate,'Fixed_Point',day)):
                #                     if file.startswith('RM'):   
                #                         shutil.copy(os.path.join(Raw_generate,'Fixed_Point', day,file),os.path.join(Raw_generate,'RAW',it))
                                            
                            
                                        
                                    
                # pdb.set_trace()
                if len(glob.glob(os.path.join(raw_dn,"%s*" % it))) > 0:                    
                    m_types.append(it)
        else:
            assert isinstance(m_type, str), "m_type must be String Type"
            m_types = [m_type]
        
        # pdb.set_trace()
        if len(m_types) > 0:
            # For every Measurement Type in the Raw Folder
            for m_type in m_types:
                transfer_measurement(m_type, update_bkp=update_bkp, lidar=lidar)
        else:
            logger.info("No measurement folders in %s." % raw_dn)

    else:  # Clean RAW directory
        clean_raw_directory()


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
    """

    """
    
    # INPUT arguments
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
    args = parser.parse_args()

    # Logging
    _, _, _, _, log_dn = paths(args.lidar)

    if not os.path.isdir(log_dn):
        create_folder(log_dn)
    log_fn = os.path.join(log_dn, "kal_transfer_manager_%s.log" % date_for_log())
    log_format = '[%(filename)s:%(lineno)s:%(funcName)s]%(levelname)s: %(message)s'
    #logging.basicConfig(format=log_format, level=logging.INFO)
    logging.basicConfig(filename=log_fn, filemode='w', format=log_format, level=logging.INFO)

    logger.info("KASCAL RAW TO 0A MANAGER")
    logger.info("[%s] Start Main" % date_for_log())
    
    pdb.set_trace()

    # RUN
    run(m_type=args.m_type, clean_raw=args.clean_raw, update_bkp=args.update_bkp, lidar=args.lidar)
  
    
    logger.info("[%s] End Main" % date_for_log())


if __name__== "__main__":
    main()
