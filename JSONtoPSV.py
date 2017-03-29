import sys
import json
import csv

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
    headerRow.append("Fix Version/s")
    headerRow.append("Product Team")
    headerRow.append("Story Point")
    return headerRow

def getInProgressDate( changelog ):
    stateChanges = list()

    sortedChangeLog = sorted(changelog, key=lambda x: x["created"])

    for change in sortedChangeLog:
        if( change["items"][0]["field"] == "status"):
            toString = change["items"][0]["toString"]
            if( toString == "In Progress" or toString == "Development In Progress"):
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

    rowdict["Created Date"] = fields["created"]
    rowdict["In Progress Date"] = getInProgressDate( issue["changelog"]["histories"])
    rowdict["Resolved Date"] = fields["resolutiondate"]
    rowdict["Fix Version/s"] = fields["fixVersions"][0]["name"] if len(fields["fixVersions"]) > 0 else ""
    rowdict["Product Team"] = fields["customfield_13321"]["value"]
    rowdict["Story Point"] = fields["customfield_11422"] if "customfield_11422" in fields else ""
    return rowdict

def getCSVrow( headerrow, rowdict ):
    row = list()

    for header in headerrow:
        row.append(rowdict[header])

    return row

if __name__ == '__main__':
    parsed = json.load(sys.stdin)

    writer = csv.writer(sys.stdout, delimiter='|', quotechar='', quoting=csv.QUOTE_NONE)

    headderrow = getheaderrow()
    writer.writerow( headderrow )

    for result in parsed:
        issues = result["issues"]
        for issue in issues:
            rowdict = getFieldsFromIssue( issue )
            row = getCSVrow( headderrow, rowdict )
            writer.writerow( row )
