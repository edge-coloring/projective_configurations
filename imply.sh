#!/bin/bash
set -euxo pipefail
cd "$(dirname "$0")"

#
# The script is used to generate configuration files enumerated in K1, K2, imply1_star, imply2_star
#
# Usage)
# bash imply.sh <level> <summary.csv> <conf-dir> <output-dir> <output-dir2>
#
# Example)
# bash imply.sh 1 reducible/summary.csv reducible/conf K1/conf imply1_star/conf
# bash imply.sh 2 K1/summary.csv K1/conf K2/conf imply2_star/conf
#

level=$1
summary=$2
confdir=$3
outdir=$4
outdir2=$5
mkdir -p "$outdir"
mkdir -p "$outdir2"

while IFS="," read f status csize conts; do
    confBaseName=$(basename $f | sed -e "s/log/conf/g")
    confFileName="$confdir/$confBaseName"
    if [ ! -e $confFileName ]; then
        continue
    fi
    if [ $status = "C" ]; then
        python3 imply.py "$level" "$confFileName" "$outdir" "$outdir2" $(echo $conts | tr -d '"' | tr '+' ' ')
    fi
done < $summary 
