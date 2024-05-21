#!/bin/bash
set -euxo pipefail
cd "$(dirname "$0")"

#
# The script is used to check Claim 7.5
#
# Usage)
# bash cut6.sh <summary.csv> <conf-dir> <output.txt> 
#
# Examples) 
# bash cut6.sh reducible/summary.csv reducible/conf cut6result.txt
# bash cut6.sh K1/summary.csv K1/conf cut6result_K1.txt
# bash cut6.sh K2/summary.csv K2/conf cut6result_K2.txt 
# bash cut6.sh imply1_star/summary.csv imply1_star/conf cut6result_imply1_star.txt 
# bash cut6.sh imply2_star/summary.csv imply2_star/conf cut6result_imply2_star.txt 
#
#

summary=$1
confdir=$2
resultFile=$3

cp /dev/null $resultFile

# read from .csv like file
while IFS="," read f status csize conts; do
    filename=$(basename $f)
    conf=${filename%.*}
    if [ $status = "C" ]; then
        python3 cut6.py "$confdir/$conf.conf" --edges $(echo $conts | tr -d '"' | tr '+' ' ') >> $resultFile
    fi
done < $summary



