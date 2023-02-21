#!/bin/bash
# EXPORT LIST
# dataset
# scale
# dtype
# dist
# m
# efc
# alpha
# file_in
# file_q
# file_gt
# ef
# rr
# beta
# th
RESULT_PATH=result/$dataset/m${m}_efc${efc}_a${alpha}

#set -x
date

mkdir -p $RESULT_PATH

echo "Running for the first ${scale} million points on ${dataset}"
param_basic="-n $((scale*1000000)) -type ${dtype} -dist ${dist}"
param_building="-ml 0.36 -m ${m} -efc ${efc} -alpha ${alpha} -b 2 -f 0 -in ${file_in}"
param_query="-q ${file_q} -g ${file_gt} -ef ${ef} -r ${rr} -beta ${beta} -th ${th}"
echo "./calc_recall ${param_basic} ${param_building} ${param_query} -out ${RESULT_PATH}/${scale}M.bin > ${RESULT_PATH}/${scale}M.log 2>&1"
./calc_recall ${param_basic} ${param_building} ${param_query} -out ${RESULT_PATH}/${scale}M.bin > ${RESULT_PATH}/${scale}M.log 2>&1
