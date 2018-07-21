#!/bin/bash


#SUBMITTING NEW JOB
command=$1

if [$command=="compile"]; then echo "HEY" 
	## compilr
elif [$command=="search"]; then echo "HELLO"
	##search
elif [$command=="download"];  then echo "!@"
	##download
elif [$command=="track"]; then ech0 "ERF"
# SOURCEFILE=$1
# TASKFILE=$2

fi







#SEARCH FUNCTIONALITY

while getopts icfutab option   
do
case "${option}"
in
i) TASKID=${OPTARG};;
c) COMPILER=${OPTARG};;
f) FLAG=${OPTARG};;
u) USER=${OPTARG};;
t) TAG=$OPTARG;;
a) DATEAFTER==$OPTARG;;
b) DATEBEFORE==$OPTARG;;
esac
done

#DOWNLOAD