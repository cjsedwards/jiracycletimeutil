import sys
import json
import csv
import datetime
import numpy

def getheaderrow():
    headerRow = list()
    headerRow.append("Key")
    headerRow.append("Project")
    headerRow.append("Summary")
    headerRow.append("Issue Type")
    headerRow.append("Status")
    headerRow.append("Resolution")
    headerRow.append("Reporter")
    headerRow.append("Creator")
    headerRow.append("Created Date")
    headerRow.append("In Progress Date")
    headerRow.append("Resolved Date")
    headerRow.append("DevEscalation Date")
    headerRow.append("Fix Version/s")
    headerRow.append("Product Team")
    headerRow.append("Story Points")
    headerRow.append("Cycle Time(Days)")
    headerRow.append("Days In Progress")
    return headerRow

def getCleanDate( jiraDate ):
    jiraDate = jiraDate[:10] if jiraDate is not None else ""
    jiraDate = datetime.datetime.strptime(jiraDate,"%Y-%m-%d").date() if len(jiraDate) > 0 else jiraDate

    return jiraDate

def getActualDaysInProgress( changelog , resolutionDate ):
    daysInProgress = 0
    statusChanges = []
    startDate = None
    endDate = None

    sortedChangeLog = sorted(changelog, key=lambda x: x["created"])

    for change in sortedChangeLog:
        if( change["items"][0]["field"] == "status"):
            toString = change["items"][0]["toString"]
            statusChanges.append( (toString , getCleanDate(change["created"])) )

    for statusChange in statusChanges:
        if( "In Progress" in statusChange[0] ):
            startDate = statusChange[1]
            endDate = None
        if("Open" in statusChange[0]):
            endDate = statusChange[1]
            daysInProgress = daysInProgress + (numpy.busday_count(startDate, endDate) if (isinstance(endDate,datetime.date) and isinstance(startDate,datetime.date)) else 0)

    if(startDate != None and endDate == None):
            endDate = resolutionDate
            daysInProgress = daysInProgress + (numpy.busday_count(startDate, endDate) if (isinstance(endDate,datetime.date) and isinstance(startDate,datetime.date)) else 0)

    if(daysInProgress == 0):
            endDate = resolutionDate
            daysInProgress = numpy.busday_count(startDate, endDate) if (isinstance(endDate,datetime.date) and isinstance(startDate,datetime.date)) else 0

    return daysInProgress

def getInProgressDate( changelog ):
    sortedChangeLog = sorted(changelog, key=lambda x: x["created"])

    for change in sortedChangeLog:
        if( change["items"][0]["field"] == "status"):
            toString = change["items"][0]["toString"]
            if( toString == "In Progress" or toString == "Development In Progress"):
                return change["created"]

    return ""

def getDevEscalationDate( changelog ):
    sortedChangeLog = sorted(changelog, key=lambda x: x["created"])

    for change in sortedChangeLog:
        if( change["items"][0]["field"] == "status"):
            toString = change["items"][0]["toString"]
            if( toString == "Live: DevEscalated" ):
                return change["created"]

    return ""

def getFieldsFromIssue( issue ):
    rowdict = dict()
    rowdict["Key"] = issue["key"]

    fields = issue["fields"]

    rowdict["Project"] = fields["project"]["name"]
    rowdict["Summary"] = fields["summary"]
    rowdict["Issue Type"] = fields["issuetype"]["name"]
    rowdict["Status"] = fields["status"]["name"]
    rowdict["Resolution"] = fields["resolution"]["name"] if fields["resolution"] is not None else ""
    rowdict["Reporter"] = fields["reporter"]["displayName"]
    rowdict["Creator"] = fields["creator"]["displayName"]

    createdDate = getCleanDate( fields["created"] )
    startDate = getCleanDate( getInProgressDate( issue["changelog"]["histories"]) )
    endDate = getCleanDate( fields["resolutiondate"] )
    cycleTime = numpy.busday_count(startDate, endDate) if (isinstance(endDate,datetime.date) and isinstance(startDate,datetime.date)) else ""

    rowdict["Created Date"] = createdDate
    rowdict["In Progress Date"] = startDate
    rowdict["DevEscalation Date"] = getCleanDate( getDevEscalationDate( issue["changelog"]["histories"]) )
    rowdict["Resolved Date"] = endDate
    rowdict["Fix Version/s"] = fields["fixVersions"][0]["name"] if len(fields["fixVersions"]) > 0 else ""
    rowdict["Product Team"] = fields["customfield_13321"]["value"] if fields["customfield_13321"] is not None else ""
    rowdict["Story Points"] = fields["customfield_11422"] if "customfield_11422" in fields else ""
    rowdict["Cycle Time(Days)"] = cycleTime
    rowdict["Days In Progress"] = getActualDaysInProgress(issue["changelog"]["histories"], endDate)
    return rowdict

def getCSVrow( headerrow, rowdict ):
    row = list()

    for header in headerrow:
        row.append(rowdict[header])

    return row

if __name__ == '__main__':
    parsed = json.load(sys.stdin)

    writer = csv.writer(sys.stdout, delimiter='|', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    headderrow = getheaderrow()
    writer.writerow( headderrow )

    for result in parsed:
        issues = result["issues"]
        for issue in issues:
            rowdict = getFieldsFromIssue( issue )
            row = getCSVrow( headderrow, rowdict )
            writer.writerow( row )
