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
mtype="TC"

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
TCfolderArray=($(find $mdir -maxdepth 1 -type d -name "${mtype}*" | sort))
#Number of the list   
nFolders=${#TCfolderArray[*]}
echo "Number of folderds:" $nFolders
for ((j=0; j<$nFolders; j++))
do
  tmpTC=${TCfolderArray[j]}
  echo "Current tmpfolder:" ${tmpTC}      
  #Path of the type[i] folder
  TCname=$(basename -- "$tmpTC")
  echo "Current TCname:" $TCname      
  #order of the type[i] file (e.g., 01, 02, ...)
  order=${TCname:2:2}     
  
  #CodeA: Code to identify letters and dots with zeros and numbers with ones    
  #First file within the first folder type[i]        
  RMfileArray=($(find $mdir/$TCname/*/*/$iletter* | sort))
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
  #Name of the destiny RS folder
  destinyFolder=$mtype"_"$datestr
  echo "destinyFolder" $destinyFolder          
  
  #Find number of sectors for the Telecover
  TC_types=($(find $tmpTC -mindepth 1 -type d | sort))
  echo "List of TC types" ${TC_types[*]}
  for ((v=0; v<${#TC_types[*]}; v++))  
  do
    #For each telecover sector
    pathTCType=${TC_types[v]}    
    tmpTCType="${pathTCType##*/}"
    echo "tmpTCType" $tmpTCType                
    
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
    NASdestinypath=${nasdir}/$year/$month/$day  #Path of the destiny folder in NAS   
    echo "NASdestinypath" $NASdestinypath
    if [[ ! -e ${NASdestinypath}/${destinyFolder} ]]; then
      mkdir --mode=777 ${NASdestinypath}/${destinyFolder}
    fi    	
    if [[ ! -e ${NASdestinypath}/${destinyFolder}/$tmpTCType ]]; then
      mkdir --mode=777 ${NASdestinypath}/${destinyFolder}/$tmpTCType
      echo "Folder path created:" ${NASdestinypath}/${destinyFolder}/$tmpTCType
    else
      echo "Folder path already exists:" ${NASdestinypath}/${destinyFolder}/$tmpTCType    
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
    BACKUPdestinypath=${bckpdir}/$year/$month/$day #Path of the destiny folder in BACKUP
    echo "BACKUPdestinypath" $BACKUPdestinypath
    if [[ ! -e ${BACKUPdestinypath}/${destinyFolder} ]]; then
      mkdir --mode=777 ${BACKUPdestinypath}/${destinyFolder}
    fi
    #Create the current backup folder
    if [[ ! -e ${BACKUPdestinypath}/${destinyFolder}/$tmpTCType ]]; then
       mkdir --mode=777 $BACKUPdestinypath/${destinyFolder}/$tmpTCType
       echo "Folder path created:" $BACKUPdestinypath/${destinyFolder}/$tmpTCType
    else
      echo "Folder path already exists:" $BACKUPdestinypath/${destinyFolder}/$tmpTCType
    fi  
        			    
    #Giving permissions to copy
    chmod 661  $mdir/$TCname/$tmpTCType
    chmod 661  ${BACKUPdestinypath}/${destinyFolder}/$tmpTCType    
    
    #Copy files to backup      
    find $mdir/$TCname/$tmpTCType/* -type f -exec cp {} ${BACKUPdestinypath}/${destinyFolder}/$tmpTCType \;
    pid=$! 
    wait $pid
    #Copy files to NAS    
    find $mdir/$TCname/$tmpTCType/* -type f -exec cp {} ${NASdestinypath}/${destinyFolder}/$tmpTCType \;
    pid=$! 
    wait $pid                
    
    #Unknonw process   
    T=$(date +"%Y%m%d%H%M")
    touch -t $T ${BACKUPdestinypath}/${destinyFolder}/$tmpTCType/*
    touch -t $T ${NASdestinypath}/${destinyFolder}/$tmpTCType/*
  done 

  #Looking for DC linked to the current TC folder, using $order variable
  DCfolder=$mdir/DC$order       
  if [[ -e $DCfolder ]]; then
    #Name of the DC folder to be created
    DCfoldername="DC_"$datestr		 
    
    #Create DC folder in BACKUPDIR
    #Create the DC path for the DC folder 
    #Create the current backup folder
    if [[ ! -e ${BACKUPdestinypath}/$DCfoldername ]]; then
       mkdir --mode=777 ${BACKUPdestinypath}/$DCfoldername
       echo "Folder path created:" ${BACKUPdestinypath}/$DCfoldername
    else
      echo "Folder path already exists:" ${BACKUPdestinypath}/$DCfoldername
    fi   
    #Create DC folder in NAS
    if [[ ! -e ${NASdestinypath}/$DCfoldername ]]; then
       mkdir --mode=777 ${NASdestinypath}/$DCfoldername
       echo "Folder path created:" ${NASdestinypath}/$DCfoldername
    else
      echo "Folder path already exists:" ${NASdestinypath}/$DCfoldername
    fi   
    
    #Copy the DC folder linked to the folder type[i] 	
    #NAS
    find $DCfolder/* -type f -exec cp {} ${NASdestinypath}/${DCfoldername} \;
    pid=$! 
    wait $pid           

    #Local backup
    find $DCfolder/* -type f -exec cp {} ${BACKUPdestinypath}/${DCfoldername} \;
    pid=$! 
    wait $pid           
  
    #Process to set the creation time of the folder
    T=$(date +"%Y%m%d%H%M")
    touch -t $T ${BACKUPdestinypath}/$DCfoldername/*
    pid=$! 
    wait $pid           
    touch -t $T ${NASdestinypath}/${DCfoldername}/*
    pid=$! 
    wait $pid               
  else 		
    echo "No DC folder linked to" $destinyFolder			 			
  fi  
  
	#Verification of the process: local to NAS and local to bckp
	#Current folder
	tmpsrc=$tmpTC/*/*/${iletter}*
  echo "tmpsrc" $tmpsrc 
	#Current folder copied to to NAS
	newdir=${NASdestinypath}/$destinyFolder/*/${iletter}*
  echo "newdir" $newdir
	#Current folder copied to backup
	bckpfolder=${BACKUPdestinypath}/$destinyFolder/*/${iletter}*
  echo "bckpfolder" $bckpfolder
	#List of folders type[i] in local
	ls $tmpsrc | xargs -n 1 basename | sort > list_local.tmp
	#List of folders type[i] in NAS
	ls $newdir | xargs -n 1 basename | sort > list_remote.tmp
	#List of folders type[i] in backup
	ls $bckpfolder | xargs -n 1 basename | sort > list_bckp.tmp
	#Difference between local and NAS
	DIFF1=$(diff list_local.tmp list_remote.tmp)
	#Difference between local and bckup
	DIFF2=$(diff list_local.tmp list_bckp.tmp)
	#If no difference then it was correctly copied
	if [[  "$DIFF1" = "" && "$DIFF2" = "" ]] 
	then
			echo "#####################################################" 
      echo $destinationFolder " successfully transfered."			
      echo "#####################################################" 
			echo "Removing folder:"$TCname
			echo "Please wait"			
			#Remove the folder in local
			rm -rf $tmpTC      
			echo $TCname " removed."  			      
	else				
		echo "Diffences betweeen the source and the destiny were found for" $destinyFolder". Please check "$TCname
    echo "DIFF between local and NAS: $DIFF1"
    echo "DIFF between local and LOCAL BACKUP: $DIFF2"
	fi	
         		
	#Remove the tmp lists
	rm list_local.tmp list_remote.tmp list_bckp.tmp
  
	#Verification of the process DC: local to NAS and local to bckp
	#Current DC folder   				
	if [[ -e $DCfolder ]]; then         
    dctmpsrc=$DCfolder/*/${iletter}*                 
		#Current folder copied to NAS
		dcnewdir=${NASdestinypath}/$DCfoldername/${iletter}*
		#Current folder copied to backup
		dcbckpfolder=${BACKUPdestinypath}/$DCfoldername/${iletter}*           
		#List of folders type[i] in local
		ls $dctmpsrc| xargs -n 1 basename | sort > list_local.tmp
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
        echo "Diffences betweeen the source and the destiny were found for" $DCfoldername". Please check DC"$order
     fi			
		#Remove the tmp lists
		rm list_local.tmp list_remote.tmp list_bckp.tmp				
  fi       
done   
