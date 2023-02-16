#!/bin/bash
# NO FUNCIONA
PYTHON=r"C:/Users/Usuario/Documents/code/venvs/gfat/bin/python"
RAW2L1_PY=C:/Users/Usuario/Documents/code/lidar_raw2l1/lidar_raw2l1.py

# SETUP
lidar="MULHACEN"

mtype="OT"
date_ini="20201111"
mtype="HF"
date_ini="20170711"
mtype="DC"
date_ini="20201111"
mtype="TC"
date_ini="20210622"
mtype="DP"
date_ini="20201111"
mtype="RS"
date_ini="20210318"

lidar="ALHAMBRA"
mtype="RS"
date_ini="20211216"

overwrite=True

# LOGGING
now=$(date '+%Y%m%d_%H%M')
LOG_DN=/home/gfat2/tareas/raw2l1_lidar
LOG_FN_PTTN=${now}_raw2_l1_${lidar}_${mtype}.log
LOG_FN=${LOG_DN}/${LOG_FN_PTTN}

# RUN
$PYTHON $RAW2L1_PY -i $date_ini -l $lidar -t $mtype -w $overwrite  #> $LOG_FN 2>&1
