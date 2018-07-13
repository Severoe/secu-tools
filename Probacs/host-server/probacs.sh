#!/bin/bash


#SUBMITTING NEW JOB

SOURCEFILE=$1
TASKFILE=$2








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