#!/bin/bash
set -x #echo on

USERNAME=`whoami`
PASSWORD=$1
STARTOFHISTORY=2017-05-15
PREVRELEASE = 6.18
OUT=~/JiraAnalysis

src=~/Source/jiracycletimeutil

#Five Sprint History - Completed Stories ( not dev escalated )
python3 $src/queryJira.py -u $USERNAME -p $PASSWORD -j https://jira.solium.com --query="filter = 33571" | python3 $src/JSONtoPSV.py > $OUT/LastFiveWeeksNoDevEscalations.txt

#Five Sprint History - Completed Stories  That were Dev Escalated
python3 $src/queryJira.py -u $USERNAME -p $PASSWORD -j https://jira.solium.com --query="filter = 33572" | python3 $src/JSONtoPSV.py > $OUT/LastFiveWeeksOnlyDevEscalations.txt
