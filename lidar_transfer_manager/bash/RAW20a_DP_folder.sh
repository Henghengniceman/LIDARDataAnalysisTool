#!/bin/bash

es_numero='^-?[0-9]+([.][0-9]+)?$'
#bash for transfering MULHACEN data from local to NAS using cp. 
lidar="Mulhacen"
#Main directory 
mdir="/drives/c/Lidar_Data/RAWS"
#backup main directory
bckpdir="/drives/g/bckp"
#NAS main directory
nasdir="/drives/y/datos/MULHACEN/0a"
#initial letter of files
iletter="R"
mtype="DP"

#logger file
printf -v dstr "%s" $(date -u "+%Y-%m-%d %H:%M:%S")
cyear=${dstr:0:4}
cmonth=${dstr:5:2}
cday=${dstr:8:2}
chour=${dstr:10:2}
cmin=${dstr:13:2}
flog=log$cyear$cmonth$cday_$chour$cmin.log
plog=$mdir/../transfer_log/$flog 

#List of type[i] folders
DPfolderArray=($(find $mdir -maxdepth 1 -type d -name "${mtype}*" | sort))
#Number of the list   
nFolders=${#DPfolderArray[*]}
echo "Number of folderds:" $nFolders
for ((j=0; j<$nFolders; j++))
do
  tmpDP=${DPfolderArray[j]}
  echo "Current tmpfolder:" ${tmpDP}      
  #Path of the type[i] folder
  DPname=$(basename -- "$tmpDP")
  echo "Current DPname:" $DPname      
  #order of the type[i] file (e.g., 01, 02, ...)
  order=${DPname:2:2}     
  
  #CodeA: Code to identify letters and dots with zeros and numbers with ones    
  #First file within the first folder type[i]        
  RMfileArray=($(find $mdir/$DPname/*/*/$iletter* | sort))
  firstFile=${RMfileArray[0]}    
  echo $firstFile 
  #Name of the first file of folder type[i]
  nameFirstFile="${firstFile##*/}"
  echo "Nombre primer archivo "$nameFirstFile           
  sum=0
  for ((w=0; w<${#nameFirstFile}; w++))
  do
    if [[ ${nameFirstFile:w:1} =~ $es_numero ]] ; then
      year=$((${nameFirstFile:w:2} + 2000))
      M1=${nameFirstFile:w+2:1}
      D1=${nameFirstFile:w+3:2}
      H1=${nameFirstFile:w+5:2}
      MIN1=${nameFirstFile:w+8:2}
      SEC1=${nameFirstFile:w+10:1}
      printf -v month "%02d" $((16#$M1))
      echo "month" $month
      printf -v day "%02d" $((10#$D1))
      echo "day" $day
      printf -v hour "%02d" $((10#$H1))
      echo "hour" $hour
      printf -v min "%02d" $((10#$MIN1)) 
      printf -v seg "%02d" $((10#$SEC1))
      index_daylocation=$w+5     
      index_firstnumber=$w       
      break   
    fi 
  done 		
  #Name to be use for saving the data:
  #nombre="$year$month$day"_"$hour$min"
  datestr=$year$month$day"_"$hour$min
  echo "datestr" $datestr
  #Name of the destination RS folder
  destinationFolder=$mtype"_"$datestr
  echo "destinationFolder" $destinationFolder          
  
  #Find number of sectors for the Telecover
  DP_types=($(find $tmpDP -mindepth 1 -type d | sort))
  echo "List of DP types" ${DP_types[*]}
  for ((v=0; v<${#DP_types[*]}; v++))  
  do
    #For each telecover sector
    pathDPType=${DP_types[v]}    
    tmpDPType="${pathDPType##*/}"
    echo "tmpDPType" $tmpDPType                
    
    if [[ "$tmpDPType" == "+45" || "$tmpDPType" == "p45" || "$tmpDPType" == "P45" ]]; then
      DPtype='P45'
    elif [[  "$tmpDPType" == "-45" || "$tmpDPType" == "n45" || "$tmpDPType" == "N45" ]]; then
      DPtype='N45'
    else
      DPtype=$tmpDPType
    fi

    # NAS   	
    #Create tree folder 
    if [[ ! -e ${nasdir}/$year ]]; then
      mkdir --mode=777 ${nasdir}/$year
    fi
    if [[ ! -e ${nasdir}/$year/$month ]]; then
      mkdir --mode=777 ${nasdir}/$year/$month
    fi   
    if [[ ! -e ${nasdir}/$year/$month/$day ]]; then
      mkdir --mode=777 ${nasdir}/$year/$month/$day
    fi  		    
    NASdestinationpath=${nasdir}/$year/$month/$day  #Path of the destination folder in NAS   
    echo "NASdestinationpath" $NASdestinationpath
    if [[ ! -e ${NASdestinationpath}/${destinationFolder} ]]; then
      mkdir --mode=777 ${NASdestinationpath}/${destinationFolder}
    fi    	
    if [[ ! -e ${NASdestinationpath}/${destinationFolder}/$DPtype ]]; then
      mkdir --mode=777 ${NASdestinationpath}/${destinationFolder}/$DPtype
      echo "Folder path created:" ${NASdestinationpath}/${destinationFolder}/$DPtype
    else
      echo "Folder path already exists:" ${NASdestinationpath}/${destinationFolder}/$DPtype    
    fi       
    
    # Creating the folder tree for the backup in the folder 'bckp'
    if [[ ! -e ${bckpdir}/$year ]]; then
       mkdir --mode=777 ${bckpdir}/$year
    fi
    if [[ ! -e ${bckpdir}/$year/$month ]]; then
       mkdir --mode=777 ${bckpdir}/$year/$month
    fi     
    if [[ ! -e ${bckpdir}/$year/$month/$day ]]; then
       mkdir --mode=777 ${bckpdir}/$year/$month/$day
    fi      
    BACKUPdestinationpath=${bckpdir}/$year/$month/$day #Path of the destination folder in BACKUP
    echo "BACKUPdestinationpath" $BACKUPdestinationpath
    if [[ ! -e ${BACKUPdestinationpath}/${destinationFolder} ]]; then
      mkdir --mode=777 ${BACKUPdestinationpath}/${destinationFolder}
    fi
    #Create the current backup folder
    if [[ ! -e ${BACKUPdestinationpath}/${destinationFolder}/$DPtype ]]; then
       mkdir --mode=777 $BACKUPdestinationpath/${destinationFolder}/$DPtype
       echo "Folder path created:" $BACKUPdestinationpath/${destinationFolder}/$DPtype
    else
      echo "Folder path already exists:" $BACKUPdestinationpath/${destinationFolder}/$DPtype
    fi  
        			    
    #Giving permissions to copy
    chmod 661  $mdir/$DPname/$tmpDPType
    chmod 661  ${BACKUPdestinationpath}/${destinationFolder}/$DPtype    
    
    #Copy files to backup      
    find $mdir/$DPname/$tmpDPType/* -type f -exec cp {} ${BACKUPdestinationpath}/${destinationFolder}/$DPtype \;
    pid=$! 
    wait $pid
    #Copy files to NAS    
    find $mdir/$DPname/$tmpDPType/* -type f -exec cp {} ${NASdestinationpath}/${destinationFolder}/$DPtype \;
    pid=$! 
    wait $pid                
    
    #Unknonw process   
    T=$(date +"%Y%m%d%H%M")
    touch -t $T ${BACKUPdestinationpath}/${destinationFolder}/$DPtype/*
    touch -t $T ${NASdestinationpath}/${destinationFolder}/$DPtype/*
  done 

  #Looking for DC linked to the current DP folder, using $order variable
  DCfolder=$mdir/DC$order       
  if [[ -e $DCfolder ]]; then
    #Name of the DC folder to be created
    DCfoldername="DC_"$datestr		 
    
    #Create DC folder in BACKUPDIR
    #Create the DC path for the DC folder 
    #Create the current backup folder
    if [[ ! -e ${BACKUPdestinationpath}/$DCfoldername ]]; then
       mkdir --mode=777 ${BACKUPdestinationpath}/$DCfoldername
       echo "Folder path created:" ${BACKUPdestinationpath}/$DCfoldername
    else
      echo "Folder path already exists:" ${BACKUPdestinationpath}/$DCfoldername
    fi   
    #Create DC folder in NAS
    if [[ ! -e ${NASdestinationpath}/$DCfoldername ]]; then
       mkdir --mode=777 ${NASdestinationpath}/$DCfoldername
       echo "Folder path created:" ${NASdestinationpath}/$DCfoldername
    else
      echo "Folder path already exists:" ${NASdestinationpath}/$DCfoldername
    fi   
    
    #Copy the DC folder linked to the folder type[i] 	
    #NAS
    find $DCfolder/* -type f -exec cp {} ${NASdestinationpath}/${DCfoldername} \;
    pid=$! 
    wait $pid           

    #Local backup
    find $DCfolder/* -type f -exec cp {} ${BACKUPdestinationpath}/${DCfoldername} \;
    pid=$! 
    wait $pid           
  
    #Process to set the creation time of the folder
    T=$(date +"%Y%m%d%H%M")
    touch -t $T ${BACKUPdestinationpath}/$DCfoldername/*
    pid=$! 
    wait $pid           
    touch -t $T ${NASdestinationpath}/${DCfoldername}/*
    pid=$! 
    wait $pid               
  else 		
    echo "No DC folder linked to" $destinationFolder			 			
  fi  
  
	#Verification of the process: local to NAS and local to bckp
	#Current folder
	tmpsrc=$tmpDP/*/*/${iletter}*
  #echo "tmpsrc" $tmpsrc 
	#Current folder copied to to NAS
	newdir=${NASdestinationpath}/$destinationFolder/*/${iletter}*
  #echo "newdir" $newdir
	#Current folder copied to backup
	bckpfolder=${BACKUPdestinationpath}/$destinationFolder/*/${iletter}*
  #echo "bckpfolder" $bckpfolder
	#List of folders type[i] in local
	#ls $tmpsrc > list_local.tmp #local
  ls $tmpsrc | xargs -n 1 basename | sort > list_local.tmp
	#List of folders type[i] in NAS
	#ls $newdir > list_remote.tmp #NAS
  ls $newdir | xargs -n 1 basename | sort > list_remote.tmp
	#List of folders type[i] in backup
	#ls $bckpfolder > list_bckp.tmp #backup
  ls $bckpfolder | xargs -n 1 basename | sort > list_bckp.tmp
	#Difference between local and NAS
	DIFF1=$(diff list_local.tmp list_remote.tmp)
  echo "DIFF1: $DIFF1"
	#Difference between local and bckup
	DIFF2=$(diff list_local.tmp list_bckp.tmp)
  echo "DIFF2: $DIFF2"
	#If no difference then it was correctly copied
	if [[  "$DIFF1" = "" && "$DIFF2" = "" ]] 
	then
			echo "#####################################################" 
      echo $destinationFolder " successfully transfered."			
      echo "#####################################################" 
			echo "Removing folder:"$DPname
			echo "Please wait"			
			#Remove the folder in local
			rm -rf $tmpDP      
			echo $DPname " removed."  			      
	else				
		echo "Diffences betweeen the source and the destination were found for" $destinationFolder". Please check "$DPname
    echo "DIFF between local and NAS: $DIFF1"
    echo "DIFF between local and LOCAL BACKUP: $DIFF2"
	fi	
         		
	#Remove the tmp lists
	#rm list_local.tmp list_remote.tmp list_bckp.tmp
  
	#Verification of the process DC: local to NAS and local to bckp
	#Current DC folder   				
	if [[ -e $DCfolder ]]; then         
		dctmpsrc=$DCfolder/*/${iletter}*                
		#Current folder copied to NAS
		dcnewdir=${NASdestinationpath}/$DCfoldername/${iletter}*
		#Current folder copied to backup
		dcbckpfolder=${BACKUPdestinationpath}/$DCfoldername/${iletter}*            
		#List of folders type[i] in local
		ls $dctmpsrc | xargs -n 1 basename | sort > list_local.tmp
		#List of folders type[i] in NAS
		ls $dcnewdir | xargs -n 1 basename | sort > list_remote.tmp
		#List of folders type[i] in backup
		ls $dcbckpfolder | xargs -n 1 basename | sort > list_bckp.tmp
		#Difference between local and NAS
		DIFF1=$(diff list_local.tmp list_remote.tmp)
		#Difference between local and bckup
		DIFF2=$(diff list_local.tmp list_bckp.tmp)
		#If no difference then it was correctly copied
		if [[  "$DIFF1" = "" && "$DIFF2" = "" ]] 
		then
				echo "#####################################################" 
				echo "Removing folder:"$DCfolder
				echo "Please wait"
				echo "#####################################################"       
				#Remove the folder in local
				rm -rf $dctmpsrc				
				echo $dctmpsrc "removed."					
	   else				
			  echo "The directory wasn't removed. Please check the backup in NAS and in" $bckpdir"."
        echo "Diffences betweeen the source and the destination were found for" $DCfoldername". Please check DC"$order
     fi			
		#Remove the tmp lists
		#rm list_local.tmp list_remote.tmp list_bckp.tmp				
  fi       
done   
