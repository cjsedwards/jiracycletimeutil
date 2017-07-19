#!/bin/bash
set -x #echo on

USERNAME=`whoami`
PASSWORD=$1
STARTOFHISTORY=2017-05-15
PREVRELEASE = 6.18
OUT=~/JiraAnalysis

src=~/Source/jiracycletimeutil

#Five Sprint History
python3 $src/queryJira.py -u $USERNAME -p $PASSWORD -j https://jira.solium.com --query="project in ('SW Product Development', 'Morgan Stanley', 'UBS') and resolved > -5w and issuetype = Story and status = Closed and resolution = Fixed" | python3 $src/JSONtoPSV.py > $OUT/AllTeamsFiveWeekHistory.txt

#Last Release
python3 $src/queryJira.py -u $USERNAME -p $PASSWORD -j https://jira.solium.com --query="project in ('SW Product Development', 'Morgan Stanley', 'UBS') and fixVersion = $PREVRELEASE and issuetype = Story and status = Closed and resolution = Fixed" | python3 $src/JSONtoPSV.py > $OUT/AllTeamsPrevRelease.txt
