import csv
import optparse
import os
import copy
import sys
import numpy
import datetime
import statistics
from math import isclose
from random import randrange

def parseOptions():
    parser = optparse.OptionParser()
    parser.add_option('-j', '--jiradata', dest='jirafilename', help='PSV file containing historical data that will be used as inputs to the model. Format output from JSONtoPSV.py')
    parser.add_option('-b', '--backlog', dest='backlogfilename', help='PSV file containing prioritized backlog. For sample format see sampleBacklog.psv')
    parser.add_option('-r', '--runs', dest='runs', help='Number of runs to execute in the Monte Carlo simulation')
    parser.add_option('-s', '--sprints', dest='sprints', help='Number of sprints in the upcoming release')
    parser.add_option('-p', '--prevsprints', dest='prevsprints', help='Number of sprints in the jiradata, used to compute avg througput')
    parser.add_option('-d', '--prevstartdate', dest='prevstartdate', help='Start of previous release (YYYY-MM-DD)')

    (options, args) = parser.parse_args()

    if( not options.jirafilename or not options.backlogfilename or not options.runs or not options.sprints or not options.prevsprints or not options.prevstartdate):
        parser.print_help()
        exit()

    if( options.jirafilename[0] == '~'):
        options.jirafilename = os.path.expanduser( options.jirafilename )
    if( options.backlogfilename[0] == '~'):
        options.backlogfilename = os.path.expanduser( options.backlogfilename )

    return options

def onlyJirasWithInProgressDate( jiradata ):
    jiradata = [x for x in jiradata if x["In Progress Date"] is not None and x["In Progress Date"] != ""]
    return jiradata

def readData( options ):
    jiradata = []
    with open( options.jirafilename, 'r') as jirafile:
        jirareader = csv.DictReader( jirafile, delimiter='|', quotechar='', quoting=csv.QUOTE_NONE )
        for row in jirareader:
            jiradata.append( row )

    backlogdata = []
    with open( options.backlogfilename, 'r') as backlogfile:
        backlogreader = csv.DictReader( backlogfile, delimiter='|', quotechar='', quoting=csv.QUOTE_NONE )
        for row in backlogreader:
            backlogdata.append( row )

    return jiradata, backlogdata

def doSprint( backlog, completed, storyCounts, pointCounts, itemCounts, options, metadata ):
    pointsCompleted = 0.0
    itemsCompleted = 0
    storiesCompleted = 0

    throughputDist = numpy.random.normal( metadata["averageThroughput"], metadata["stddevThroughput"], 10)
    #avgThroughput = metadata["averageThroughput"]
    #throughputDist = [avgThroughput - 2, avgThroughput - 1, avgThroughput, avgThroughput + 1, avgThroughput + 2]
    throughput = throughputDist[randrange(len(throughputDist))]
    throughput = int(round( throughput, 0 ))
    throughput = throughput if throughput > 0 else 0

    for items in range( 0, throughput):
        if( len(backlog) == 0 ):
            break;

        item = backlog.pop(0)
        completed.append( item )

        itemsCompleted = itemsCompleted + 1
        if( item["Issue Type"] == "Story" and item["Story Points"] != ""):
            storiesCompleted = storiesCompleted + 1
            pointsCompleted = pointsCompleted + float(item["Story Points"])

    storyCounts.append( storiesCompleted )
    pointCounts.append( pointsCompleted )
    itemCounts.append( itemsCompleted )

def doRun( backlog, options, metadata ):
    backlog = copy.deepcopy(backlog)
    runResults = dict()

    completed = []
    storyCounts = []
    pointCounts = []
    itemCounts = []
    completedPerSprint = []
    for sprint in range(0, int(options.sprints)):
        completedInSprint = []

        doSprint( backlog, completedInSprint, storyCounts, pointCounts, itemCounts, options, metadata )

        completed.extend( completedInSprint )
        completedPerSprint.append( [issue["Key"] for issue in completedInSprint] )

    runResults["completed"] = [issue["Key"] for issue in completed]
    runResults["storyCounts"] = storyCounts
    runResults["pointCounts"] = pointCounts
    runResults["itemCounts"] = itemCounts
    runResults["completedPerSprint"] = completedPerSprint

    return runResults

def computeChanceOfCompletion( key, allruns, sprint ):
    count = 0

    for run in allruns:
        for i in range( 0, int(sprint+1)):
            if key in run["completedPerSprint"][i]:
                count = count + 1
                break

    return count / len(allruns)

def computeSprintStats( sprint, allruns, statname ):
    counts = []

    for run in allruns:
        counts.append( run[statname][sprint] )

    counts.sort()

    stats = dict()
    ncounts = numpy.array( counts )
    stats["P10"] = numpy.percentile( ncounts, 10)
    stats["P50"] = numpy.percentile( ncounts, 50)
    stats["P90"] = numpy.percentile( ncounts, 90)

    return stats

def computeForecast( allruns, options, statname ):
    result = dict()

    result["P10"] = []
    result["P50"] = []
    result["P90"] = []
    for sprint in range( 0, int(options.sprints) ):
        sprintstats = computeSprintStats( sprint, allruns, statname )
        result["P10"].append( sprintstats["P10"] )
        result["P50"].append( sprintstats["P50"] )
        result["P90"].append( sprintstats["P90"] )

    return result

def computeStats( backlog, allruns, options ):
    stats = dict()

    stats["completionChance"] = dict()
    completionChance = stats["completionChance"]

    for item in backlog:
        key = item["Key"]
        completionChance[key] = []
        for sprint in range( 0, int(options.sprints)):
            completionChance[key].append( computeChanceOfCompletion( key, allruns, sprint ) )

    stats["storyForecasts"] = computeForecast( allruns, options, "storyCounts")
    stats["pointForecasts"] = computeForecast( allruns, options, "pointCounts")
    stats["itemForecasts"] = computeForecast( allruns, options, "itemCounts")

    return stats

def parseDate( dateString ):
    return datetime.datetime.strptime(dateString,"%Y-%m-%d").date()

def throughputPerSprint( jiradata, options ):
    result = []

    startOfSprint = parseDate( options.prevstartdate )

    for sprint in range( 0, int(options.prevsprints) ):
        endOfSprint = startOfSprint + datetime.timedelta(days=7)
        completedIssuesInSprint = [issue for issue in jiradata if parseDate(issue["Resolved Date"]) < endOfSprint and parseDate(issue["Resolved Date"]) >= startOfSprint]
        completedStoriesInSprint = [issue for issue in completedIssuesInSprint if issue["Issue Type"] == "Story"]
        completedPointsInSprint = [float(issue["Story Points"]) for issue in completedIssuesInSprint if issue["Story Points"] != ""]

        result.append( len (completedStoriesInSprint) )

        startOfSprint = endOfSprint

    return result

def printForecasts( finalStats, forecastName ):
    forecast = finalStats[forecastName]
    print( forecastName )
    writer.writerow( ["P10", "P50", "P90"])
    P10 = forecast["P10"]
    P50 = forecast["P50"]
    P90 = forecast["P90"]
    count = 0
    for value in finalStats["storyForecasts"]["P10"]:
        writer.writerow( [P10[count], P50[count], P90[count]])
        count = count + 1

if __name__ == '__main__':
    options = parseOptions()
    jiradata, backlogdata = readData( options )

    jiradata = onlyJirasWithInProgressDate( jiradata )

    metadata = dict()
    metadata["throughputPerSprint"] = throughputPerSprint( jiradata, options )
    metadata["averageThroughput"] = statistics.mean( metadata["throughputPerSprint"])
    metadata["stddevThroughput"] = statistics.stdev( metadata["throughputPerSprint"])

    allruns = []
    for run in range( 0, int(options.runs)):
        runResult = doRun( backlogdata, options, metadata )
        allruns.append( runResult )

    finalStats = computeStats( backlogdata, allruns, options )

    writer = csv.writer(sys.stdout)
    headerrow = []
    headerrow.append( "Key")
    for sprint in range( 0, int(options.sprints) ):
        headerrow.append( "Sprint " + str(sprint + 1) )
    writer.writerow( headerrow )

    for key, value in finalStats["completionChance"].items():
        row = []
        row.append( key )
        row.extend( value )
        writer.writerow(row)

    printForecasts( finalStats, "storyForecasts" )
    printForecasts( finalStats, "pointForecasts" )
    printForecasts( finalStats, "itemForecasts" )
