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
mtype="HF"

#logger file
printf -v dstr "%s" $(date -u "+%Y-%m-%d %H:%M:%S")
cyear=${dstr:0:4}
cmonth=${dstr:5:2}
cday=${dstr:8:2}
chour=${dstr:10:2}
cmin=${dstr:13:2}
cdate="${cyear}-${cmonth}-${cday} ${chour}:${cmin}:00"
flog=log$cyear$cmonth$cday_$chour$cmin.log
plog=$mdir/../transfer_log/$flog 

#List of type[i] folders
RSfolderArray=($(find $mdir -maxdepth 1 -type d -name "${mtype}*" | sort))
#Number of the list   
nFolders=${#RSfolderArray[*]}
echo "Number of folderds:" $nFolders
for ((j=0; j<$nFolders; j++))
do
	tmpRS=${RSfolderArray[j]}
	echo "Current tmpfolder:" ${tmpRS}      
	#Path of the type[i] folder
	RSname=$(basename -- "$tmpRS")
	echo "Current RSname:" $RSname      
	#order of the type[i] file (e.g., 01, 02, ...)
	order=${RSname:2:2}     
  
	#CodeA: Code to identify letters and dots with zeros and numbers with ones    
	#First file within the first folder type[i]        
	RMfileArray=($(find $mdir/$RSname/*/$iletter* | sort))
	firstFile=${RMfileArray[0]}    

	if [[ ! -z $firstFile ]];then
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
		  
		# NAS Backup  	
		#Create tree folder
		#Option A
		if [[ ! -e ${nasdir}/$year/$month/$day ]]; then
			mkdir --mode=777 -p ${nasdir}/$year/$month/$day
		fi  		
	
		#Path of the destination folder in NAS   
		NASdestinationpath=${nasdir}/$year/$month/$day    
		echo "NASdestinationpath" $NASdestinationpath    	
		if [[ ! -e ${NASdestinationpath}/${destinationFolder} ]]; then
			mkdir -m777 ${NASdestinationpath}/${destinationFolder}
			echo "Folder path created:" ${NASdestinationpath}/${destinationFolder}
		else
			echo "Folder path already exists:" ${NASdestinationpath}/${destinationFolder}   
		fi	
		
		# Creating the folder tree for the backup in the folder 'bckp'
		if [[ -e ${NASdestinationpath}/${destinationFolder} ]]; then			
			if [[ ! -e ${bckpdir}/$year ]]; then
				mkdir --mode=777 ${bckpdir}/$year
			fi
			if [[ ! -e ${bckpdir}/$year/$month ]]; then
				mkdir --mode=777 ${bckpdir}/$year/$month
			fi     
			if [[ ! -e ${bckpdir}/$year/$month/$day ]]; then
				mkdir --mode=777 ${bckpdir}/$year/$month/$day
			fi      
			#Path of the destination folder in BACKUP
			BACKUPdestinationpath=${bckpdir}/$year/$month/$day
			echo "BACKUPdestinationpath" $BACKUPdestinationpath
			#Create the current backup folder
			if [[ ! -e $BACKUPdestinationpath/${destinationFolder} ]]; then
				mkdir --mode=777 $BACKUPdestinationpath/${destinationFolder}
				echo "Folder path created:" $BACKUPdestinationpath/${destinationFolder}
			else
				echo "Folder path already exists:" $BACKUPdestinationpath/${destinationFolder}
			fi  
							
			#Give permissions to copy
			chmod 661 $mdir/$RSname/*
			chmod 661 ${BACKUPdestinationpath}/${destinationFolder}
			# chmod 661 ${NASdestinationpath}/${destinationFolder}

			#Copy files to backup  
			find $mdir/$RSname -type f -exec cp {} ${BACKUPdestinationpath}/${destinationFolder} \;
			pid=$! 
			wait $pid
			#Copy files to NAS
			find $mdir/$RSname -type f -exec cp {} ${NASdestinationpath}/${destinationFolder} \;
			pid=$! 
			wait $pid                

			#Set creation time of the folder
			T=$(date +"%Y%m%d%H%M")
			touch -t $T ${BACKUPdestinationpath}/${destinationFolder}/*
			touch -t $T ${NASdestinationpath}/${destinationFolder}/*
					
			#Looking for DC linked to the RS folder
			DCfolder=$mdir/DC$order       
			if [[ -e $DCfolder ]]; then
				#Name of the DC folder to be created
				DCfoldername="DC_"$datestr		 
				
				#Create DC folder in BACKUPDIR
				#Create the DC path for the DC folder 
				#Create the current backup folder
				if [[ ! -e ${BACKUPdestinationpath}/$DCfoldername ]]; then
					mkdir -m777 ${BACKUPdestinationpath}/$DCfoldername
					echo "Folder path created:" ${BACKUPdestinationpath}/$DCfoldername
				else
					echo "Folder path already exists:" ${BACKUPdestinationpath}/$DCfoldername
				fi   
				#Create DC folder in NAS
				if [[ ! -e ${NASdestinationpath}/$DCfoldername ]]; then
					mkdir -m777 ${NASdestinationpath}/$DCfoldername
					echo "Folder path created:" ${NASdestinationpath}/$DCfoldername
				else
					echo "Folder path already exists:" ${NASdestinationpath}/$DCfoldername
				fi   
				
				#Copy the DC folder linked to the folder type[i] 	
				#NAS backup
				find $DCfolder/* -type f -exec cp {} ${NASdestinationpath}/${DCfoldername} \;
				pid=$! 
				wait $pid           

				#Local backup
				find $DCfolder/* -type f -exec cp {} ${BACKUPdestinationpath}/${DCfoldername} \;
				pid=$! 
				wait $pid           
			
				#Uknonw process
				#T=$(date +"%Y%m%d%H%M")
				#touch -t $T ${BACKUPdestinationpath}/$DCfoldername/*
				#pid=$! 
				#wait $pid           
				#touch -t $T ${NASdestinationpath}/${DCfoldername}/*
				#pid=$! 
				#wait $pid               
			else 		
				echo "No DC folder linked to" $destinationFolder			 			
			fi
			
			#Verification of the process: local to NAS and local to bckp
			#Current folder
			tmpsrc=$tmpRS
			echo "tmpsrc" $tmpsrc 
			#Current folder copied to to NAS
			newdir=${NASdestinationpath}/$destinationFolder
			echo "newdir" $newdir
			#Current folder copied to backup
			bckpfolder=${BACKUPdestinationpath}/$destinationFolder
			echo "bckpfolder" $bckpfolder
			list=($(find $mdir/$RSname/* -type f -name "$iletter*.*"| sort))
			echo "Size list ${list[@]}"
			last=$((${#list[@]}-1))			
			echo $last			
			lastfile=$(basename -- "${list[$((last))]}")		
			echo $lastfile						
			lyear=$((${lastfile:w:2} + 2000))
			echo $lyear
			echo "last year" $lyear
			M1=${lastfile:w+2:1}
			D1=${lastfile:w+3:2}
			H1=${lastfile:w+5:2}
			MIN1=${lastfile:w+8:2}
			SEC1=${lastfile:w+10:1}			
			echo "line 219: Month1 $M1"
			printf -v lmonth "%02d" $((16#$M1))
			#echo "last month" $lmonth
			printf -v lday "%02d" $((10#$D1))
			#echo "last day" $lday
			printf -v lhour "%02d" $((10#$H1))
			#echo "last hour" $lhour
			printf -v lmin "%02d" $((10#$MIN1)) 
			#echo "last minute" $lmin
			#printf -v lsec "%02d" $((10#$SEC1))				
			#echo "last second" $lsec
			lastdate="${lyear}-${lmonth}-${lday} ${lhour}:${lmin}:00"
			numldate=$(date -d"$lastdate" +%s)
			if [[ ${#list[@]} -gt 0 ]]; then
				blast=$((${#list[@]}-2))			
				#echo $blast			
				blastfile=$(basename -- "${list[$((blast))]}")
				#echo $blastfile						
				blyear=$((${blastfile:w:2} + 2000))
				echo "blast year" $blyear
				M1=${blastfile:w+2:1}
				D1=${blastfile:w+3:2}
				H1=${blastfile:w+5:2}
				MIN1=${blastfile:w+8:2}
				SEC1=${blastfile:w+10:1}
				echo "blast second original" $SEC1
				printf -v blmonth "%02d" $((16#$M1))
				echo "blast month" $lmonth
				printf -v blday "%02d" $((10#$D1))
				echo "blast day" $lday
				printf -v blhour "%02d" $((10#$H1))
				echo "blast hour" $lhour
				printf -v blmin "%02d" $((10#$MIN1)) 
				echo "blast minute" $blmin
				blastdate="${blyear}-${blmonth}-${blday} ${blhour}:${blmin}:00"		
				numbldate=$(date -d"$blastdate" +%s)
			else				
				numbldate=$((numldate-300))
			fi
			timegap=$(($numldate-$numbldate))		
			threshold_gap=2*${timegap}
			echo "Timegap between last ($lastdate [$numldate]) and before last file ($blastdate [$numbldate]) is $timegap"						
			numcdate=$(date -d"$cdate" +%s)			
			diffdate=$(($numcdate-$numldate))			
			echo "Comparing last file date ($lastdate [$numldate]) against current date ($cdate [$numcdate]): difference is $diffdate"			
			if [[  $diffdate -gt $threshold_gap ]]; then		
				echo "#####################################################" 
				echo "More than twice of the session time resolution without new measurement files..."
				echo "Measurement session considered finished."
				echo "#####################################################"       
				#List of folders type[i] in local
				ls $tmpsrc > list_local.tmp #local
				#List of folders type[i] in NAS
				ls $newdir > list_remote.tmp #NAS
				#List of folders type[i] in backup
				ls $bckpfolder > list_bckp.tmp #backup
				#Difference between local and NAS
				DIFF1=$(diff list_local.tmp list_remote.tmp)
				#Difference between local and bckup
				DIFF2=$(diff list_local.tmp list_bckp.tmp)
				#If no difference then it was correctly copied
				if [[  "$DIFF1" = "" && "$DIFF2" = "" ]]; then				
					echo $destinationFolder " successfully transfered."	
					echo "Removing folder:"$RSname
					echo "Please wait"					
					#Remove the folder in local
					rm -rf $tmpRS					
					echo $RSname " removed."  			
					controRSremoved=1;
				else							
					echo "Diffences betweeen " $RSname "(source) and "$destinationFolder "(destination) were found. Please check"
					controRSremoved=0;
				fi	
							
				#Remove the tmp lists
				rm list_local.tmp list_remote.tmp list_bckp.tmp			
				echo "Removing folder: $RSname"
				echo "Please wait"
				echo "#####################################################"       
				#Remove the folder in local
				rm -rf $tmpRS
				#rm -rf $tmpRS
				echo $RSname " removed."  			
				sessionClosed=1;
			else							
				echo "This sesssion seems to be running. This folder will not be removed."
				sessionClosed=0;
			fi	

			#Verification of the process DC: local to NAS and local to bckp
			#Current DC folder   							     
			if [[ -e $DCfolder ]]; then         
				if [[ $sessionClosed == 1 ]]; then   
					dctmpsrc=$DCfolder                 
					#Current folder copied to NAS
					dcnewdir=${NASdestinationpath}/$DCfoldername
					#Current folder copied to backup
					dcbckpfolder=${BACKUPdestinationpath}/$DCfoldername              
					#List of folders type[i] in local
					ls $dctmpsrc > list_local.tmp #local
					#List of folders type[i] in NAS
					ls $dcnewdir > list_remote.tmp #NAS
					#List of folders type[i] in backup
					ls $dcbckpfolder > list_bckp.tmp #backup
					#Difference between local and NAS
					DIFF1=$(diff list_local.tmp list_remote.tmp)
					#Difference between local and bckup
					DIFF2=$(diff list_local.tmp list_bckp.tmp)
					#If no difference then it was correctly copied
					if [[  "$DIFF1" = "" && "$DIFF2" = "" ]]; then
							echo "#####################################################" 
							echo "Removing folder:"$DCfolder
							echo "Please wait"
							echo "#####################################################"       
							#Remove the folder in local
							rm -rf $dctmpsrc				
							echo $dctmpsrc "removed."	
					else				
						echo "Diffences betweeen " $DCfoldername "(source) and DC"$order "(destination) were found. Please check"
					fi			
					#Remove the tmp lists
					rm list_local.tmp list_remote.tmp list_bckp.tmp				
				else
					echo "DC$order not removed because session $RSname is still open."
				fi				
			fi
		else
			echo "Folder "  ${NASdestinationpath}/${destinationFolder} " not found."						
		fi
	else
		echo "Folder " $RSname " is empty."
		echo "#####################################################" 
		echo "Removing folder:"$RSname
		echo "Please wait"
		echo "#####################################################"       
		#Remove the folder in local
		rm -rf $tmpRS
		echo $RSname " removed." 			
	fi	
done