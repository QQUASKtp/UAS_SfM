# This script detects tie/key points, orients imagery in relative space then
# adjusts using GNSS data 

# Author Ciaran Robb
# Aberystwyth University

#https://github.com/Ciaran1981/Sfm
# example:
# Orientation.sh -e JPG -u "30 +north" -c Fraser -t Log_edited.csv -s sub.csv




while getopts ":e:u:i:c:t:s:h:" o; do  
  case ${o} in
    h)
      echo "Carry out feature extraction and orientation of images"
      echo "Usage: Orientation.sh -e JPG -u 30 +north -c Fraser -t weeboats.csv  " 
      echo "	-e {EXTENSION}     : image file type (JPG, jpg, TIF, png..., default=JPG)."
      echo "	-u UTMZONE       : UTM Zone of area of interest. Takes form 'NN +north(south)'"
      echo "	-i SIZE         : resize of imagery eg - 2000"
      echo "	-c CALIB        : Camera calibration model - e.g. RadialBasic, Fraser etc"
      echo "    -t CSV        : text file usually csv with mm3d formatting"
      echo "    -s SUB        : a subset  csv for pre-calibration of orientation"      
      echo "	-h	             : displays this message and exits."
      echo " "  
      exit 0
      ;;    
	e)
      EXTENSION=${OPTARG}
      ;;
	u)
      UTM=${OPTARG}
      ;;
 	i)
      SIZE=${OPTARG}
      ;; 
 	c)
      CALIB=${OPTARG}
      ;;          
    t)
      CSV=${OPTARG}
      ;; 
    s)
      SUB=${OPTARG}
      ;;           
    \?)
      echo "Orientation.sh: Invalid option: -${OPTARG}" >&1
      exit 1
      ;;
    :)
      echo "Orientation.sh: Option -${OPTARG} requires an argument." >&1
      exit 1
      ;;
  esac
done

shift $((OPTIND-1))

#selection=
#until [  "$selection" = "1" ]; do
#    echo "
#    CHECK (carefully) PARAMETERS
#	-e : image extenstion/file type $EXTENSION
#	-u : UTM Zone of area of interest $UTM
#	-i : resize of imagery $SIZE
#	-c : Camera calibration model $CALIB
#	-m : Whether to manually mask the sparse cloud $MASK
#	-t : gps text file usually csv with mm3d formatting $CSV
#	-s : a subset gps csv for pre-calibration of orientation $SUB

#    echo 
#    CHOOSE BETWEEN
#    1 - Continue with these parameters
#    0 - Exit program
#    2 - Help
#"
#    echo -n "Enter selection: "
#    read selection
#    echo ""
#    case $selection in
#        1 ) echo "Let's process now" ; continue ;;
#        0 ) exit ;;
#    	2 ) echo "
#		For help use : Orientation.sh -h
#	   " >&1
#	   exit 1 ;;
#        * ) echo "
#		Only 0 or 1 are valid choices
#		For help use : Orientation.sh -h
#		" >&1
#		exit 1 ;;
#    esac
#done



# bramor
#mm3d SetExif ."*{EXTENSION}" F35=45 F=30 Cam=ILCE-6000  
# # A PHANTOM 4
# mm3d SetExif .*JPG F35=20 F=3.6 Cam=DJI
#exiftool *.JPG | grep "Focal Length"
# magick mogrify -resize 50%
# iphone se6
#mm3d SetExif F35=29 F=4.2 mm 
#exiftool -TagsFromFile fromImage.jpg toImage.jpg
# mm3d SetExif ."*{EXTENSION}" F35=25 F=4.5

#create UTM file (after deleting any existing one)
rm SysUTM.xml
echo "<SystemeCoord>                                                                                              " >> SysUTM.xml
echo "         <BSC>                                                                                              " >> SysUTM.xml
echo "            <TypeCoord>  eTC_Proj4 </TypeCoord>                                                             " >> SysUTM.xml
echo "            <AuxR>       1        </AuxR>                                                                   " >> SysUTM.xml
echo "            <AuxR>       1        </AuxR>                                                                   " >> SysUTM.xml
echo "            <AuxR>       1        </AuxR>                                                                   " >> SysUTM.xml
echo "            <AuxStr>  +proj=utm +zone="$UTM "+ellps=WGS84 +datum=WGS84 +units=m +no_defs   </AuxStr>        " >> SysUTM.xml
echo "                                                                                                            " >> SysUTM.xml
echo "         </BSC>                                                                                             " >> SysUTM.xml
echo "</SystemeCoord>                                                                                             " >> SysUTM.xml
  

#mm3d SetExif ."*JPG" F35=45 F=30 Cam=ILCE-6000  
# mogrify -resize 30% *.JPG
#mogrify -resize 2000 *.JPG

if [  -f "${CSV}" ]; then 
    echo "using csv file ${CSV}"  
    mm3d OriConvert OriTxtInFile ${CSV} RAWGNSS_N ChSys=DegreeWGS84@SysUTM.xml MTD1=1  NameCple=FileImagesNeighbour.xml CalcV=1
    sysCort_make.py -csv ${CSV} -d " "  
else 
    echo "using exif data"
    mm3d XifGps2Txt .*${EXTENSION} 
    #Get the GNSS data out of the images and convert it to a xml orientation folder (Ori-RAWGNSS), also create a good RTL (Local Radial Tangential) system.
    mm3d XifGps2Xml .*${EXTENSION} RAWGNSS_N
    mm3d OriConvert "#F=N X Y Z" GpsCoordinatesFromExif.txt RAWGNSS_N ChSys=DegreeWGS84@RTLFromExif.xml MTD1=1 NameCple=FileImagesNeighbour.xml CalcV=1
fi 


if [  -n "${SIZE}" ]; then
    echo "resizing to ${SIZE} for tie point detection"
    # mogrify -path Sharp -sharpen 0x3  *.JPG # this sharpens very well worth doing
    mogrify -resize ${SIZE} *.${EXTENSION}
fi

mm3d Tapioca File FileImagesNeighbour.xml -1  @SFS


mm3d Schnaps .*${EXTENSION} MoveBadImgs=1
# The sh doesn't seem to work in PIMs etc so best to rename and thus we have reduced set
mv Homol HomolInit1
mv Homol_mini Homol

#Compute Relative orientation (Arbitrary system)

if [  -n "${SUB}" ]; then
    echo "using calibration subset"
    calib_subset.py -folder $PWD -algo ${CALIB}  -csv ${SUB} -ext .${EXTENSION} 
else
    mm3d Martini .*${EXTENSION}

    mm3d Tapas ${CALIB} .*${EXTENSION} Out=Arbitrary InCal=Martini | tee ${CALIB}RelBundle.txt
    echo " orientation using whole dataset"
fi    


#Visualize relative orientation

mm3d AperiCloud .*${EXTENSION} Ori-Arbitrary 

# This is worth doing to get rid of spurious points on fringes and below the assumed plain
#if [ "${MASK}" = true ]; then
#    echo "masking initial orientation"
#    mm3d AperiCloud .*${EXTENSION} Ori-Arbitrary SH=_mini WithCam=0 Out=NoCams.ply
#    mm3d SaisieMasqQT NoCams.ply
#    read -rsp $'Once mask is saved press any key to continue...\n' -n1 key
#    mm3d HomolFilterMasq .*${EXTENSION}  OriMasq3D=Ori-Arbitrary/ Masq3D=NoCams.ply
    # rename homologous points, the filtered one will be seen as the default
#    mv Homol HomolInit2
#    mv HomolMasqFiltered/ Homol
    #mm3d Tapas ${CALIB} .*${EXTENSION} InOri=Ori-Arbitrary/ Out=ArbitraryM
    #mm3d CenterBascule .*${EXTENSION} ArbitraryM RAWGNSS_N Ground_Init_RTL
#else
    #Transform to  RTL system
mm3d CenterBascule .*${EXTENSION} Arbitrary RAWGNSS_N Ground_Init_RTL
#fi

#Visualize Ground_RTL orientation
mm3d AperiCloud .*${EXTENSION} Ori-Ground_Init_RTL 

#Bundle adjust using both camera positions and tie points (number in EmGPS option is the quality estimate of the GNSS data in meters)
 
#Change system to final cartographic system  
if [  -n "${CSV}" ]; then 
    mm3d Campari .*${EXTENSION} Ground_Init_RTL Ground_UTM EmGPS=[RAWGNSS_N,1] AllFree=1  | tee ${CALIB}GnssBundle.txt
else
    mm3d Campari .*${EXTENSION} Ground_Init_RTL Ground_RTL EmGPS=[RAWGNSS_N,1] AllFree=1 | tee ${CALIB}GnssBundle.txt
    mm3d ChgSysCo  .*${EXTENSION} Ground_RTL RTLFromExif.xml@SysUTM.xml Ground_UTM
    mm3d OriExport Ori-Ground_UTM/.*xml CameraPositionsUTM.txt AddF=1
fi


mm3d AperiCloud .*${EXTENSION} Ground_UTM WithCam=0
