#!/bin/bash

echo "Starting transfer for RS## folders" 
bash /drives/c/Lidar_data/raw20a/RAW20a_RS.sh
pid=$!
wait $pid
echo "Ending transfer for RS## folders"
echo "Starting transfer for DP## folders"
bash /drives/c/Lidar_data/raw20a/RAW20a_DP.sh
pid=$!
wait $pid
echo "Ending transfer for DP## folders"
echo "Starting transfer for TC## folders"
bash /drives/c/Lidar_data/raw20a/RAW20a_TC.sh
pid=$!
wait $pid
echo "Ending transfer for TC## folders"
echo "Starting transfer for OT## folders"
bash /drives/c/Lidar_data/raw20a/RAW20a_OT.sh
pid=$!
wait $pid
echo "Ending transfer for OT## folders"
echo "Starting transfer for HF## folders"
bash /drives/c/Lidar_data/raw20a/RAW20a_HF.sh
echo "Ending transfer for HF## folders"
echo "launch_RAW20a finished"
