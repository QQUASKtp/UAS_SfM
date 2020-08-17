# Author Ciaran Robb
# Aberystwyth University
# Using GDAL and OSSIM, create a large scale ortho-mosaic from a set of smaller ones generated by the batch fucntions here:
# https://github.com/Ciaran1981/Sfm


# add default values
FOLDER=$PWD  
MTYPE=ossimMaxMosaic
utm_set=false
OUT=DSMmosaic.tif


 
while getopts "f:u:mt:o:h" opt; do  
  case $opt in
    h)
      echo "Mosiac dsms."
      echo "dsmmosaic.sh -f $PWD -u '30 +north' -mt ossimFeatherMosaic -o outmosaic.tif"
      echo "	-f FOLDER     : MicMac working directory."
      echo "	-u UTMZONE       : UTM Zone of area of interest. Takes form 'NN +north(south)'"
      echo " -mt MTYPE        : OSSIM mosaicing type e.g. ossimBlendMosaic ossimMaxMosaic ossimImageMosaic ossimClosestToCenterCombiner ossimBandMergeSource ossimFeatherMosaic" 
      echo "	-o OUT       : Output mosaic e.g. mosaic.tif"      
      echo "	-h	             : displays this message and exits."
      
      echo " " 
      exit 0
      ;;    
	f)
      FOLDER=$OPTARG 
      ;;
	u)
      UTM=$OPTARG
      utm_set=true
      ;;
	mt)
      MTYPE=$OPTARG
      ;;                        
	o)
      OUT=$OPTARG
      ;;        
    \?)
      echo "gpymicmac.sh: Invalid option: -$OPTARG" >&1
      exit 1
      ;;
    :)
      echo "gpymicmac.sh: Option -$OPTARG requires an argument." >&1
      exit 1
      ;;
  esac
done

# georef the dsms.....
echo "geo-reffing DSMs"  
#finalDEMs=($(ls Z_Num*_DeZoom*_STD-MALT.tif)) 
for f in $FOLDER/MaltBatch/*tile*/*tile*/Z_Num7_DeZoom2_STD-MALT.tif; do
    gdal_edit.py -a_srs "+proj=utm +zone=$UTM  +ellps=WGS84 +datum=WGS84 +units=m +no_defs" "$f"; done

# mask_dsm.py -folder $PWD -n 20 -z 1 -m 1
#  This will assume a zoom level 2 
mask_dsm.py -folder MaltBatch 

echo "generating image histograms"
find $FOLDER/MaltBatch/*tile*/*tile*/Z_Num7_DeZoom2_STD-MALT.tif | parallel "ossim-create-histo -i {}" 

echo "constructing large mosaic"
ossim-orthoigen --combiner-type ossimMaxMosaic  $FOLDER/MaltBatch/*tile*/*tile*/Z_Num7_DeZoom2_STD-MALT.tif $OUT
