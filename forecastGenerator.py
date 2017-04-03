import csv
import optparse
import os
import copy
import numpy
from statistics import median
from math import isclose

def parseOptions():
    parser = optparse.OptionParser()
    parser.add_option('-j', '--jiradata', dest='jirafilename', help='PSV file containing historical data that will be used as inputs to the model. Format output from JSONtoPSV.py')
    parser.add_option('-b', '--backlog', dest='backlogfilename', help='PSV file containing prioritized backlog. For sample format see sampleBacklog.psv')
    parser.add_option('-w', '--wiplimit', dest='wiplimit', help='Max number of work items in progress.')
    parser.add_option('-r', '--runs', dest='runs', help='Number of runs to execute in the Monte Carlo simulation')
    parser.add_option('-s', '--sprints', dest='sprints', help='Number of sprints in the upcoming release')
    parser.add_option('-p', '--prevsprints', dest='prevsprints', help='Number of sprints in the jiradata, used to compute avg througput')

    (options, args) = parser.parse_args()

    if( not options.jirafilename or not options.backlogfilename or not options.wiplimit or not options.runs or not options.sprints or not options.prevsprints):
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

def splitIssues( jiradata ):
    lives = [x for x in jiradata if "Live" in x["Project"]]
    notlives = [x for x in jiradata if not ("Live" in x["Project"])]

    bugs = [x for x in notlives if x["Issue Type"] == "Bug"]
    stories = [x for x in notlives if x["Issue Type"] != "Bug"]

    return lives, bugs, stories

def getMetaData( issues ):
    return 5

def doRun( backlog, options, metadata ):
    backlog = copy.copy(backlog)
    runResults = dict()

    completed = []
    storyCounts = []
    pointCounts = []
    itemCounts = []
    for sprint in range(0, int(options.sprints)):
        pointsCompleted = 0.0
        itemsCompleted = 0
        storiesCompleted = 0
        for items in range( 0, metadata["throughput"]):
            if( len(backlog) == 0 ):
                break;

            itemsCompleted = itemsCompleted + 1
            if( backlog[0]["Issue Type"] == "Story" and backlog[0]["Story Points"] != ""):
                storiesCompleted = storiesCompleted + 1
                pointsCompleted = pointsCompleted + float(backlog[0]["Story Points"])

            completed.append( backlog.pop(0) )


        completedAtEnd = len(completed)
        storyCounts.append( storiesCompleted )
        pointCounts.append( pointsCompleted )
        itemCounts.append( itemsCompleted )

    runResults["completed"] = [issue["Key"] for issue in completed]
    runResults["storyCounts"] = storyCounts
    runResults["pointCounts"] = pointCounts
    runResults["itemCounts"] = itemCounts

    return runResults

def computeChanceOfCompletion( key, allruns ):
    count = 0
    for run in allruns:
        if key in run["completed"]:
            count = count + 1

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
        completionChance[key] = computeChanceOfCompletion( key, allruns )


    stats["storyForecasts"] = computeForecast( allruns, options, "storyCounts")
    stats["pointForecasts"] = computeForecast( allruns, options, "pointCounts")
    stats["itemForecasts"] = computeForecast( allruns, options, "itemCounts")

    return stats

def storyPointFloat( storypoint ):
    if( storypoint is None or storypoint == "" ):
        return 0

    return float( storypoint )

# "Size" here means "The number of small things" that an issue was comprised
# of, calculated roughly using how long it took relative to other things
# that were completed
# Note: This is different than story points, because points are an estimate
#       and this is based on actual time it took to complete something
# Second Note: I recognize this is kind of janky because I'm using cycle time
#              to estimate size and that is wrong, but again, this is a rough
#              way of doing with lack of something better.
def addSizeToAllIssues( jiradata ):
    cycleTimeOfOneSmallThing = 1.0 # worst case we use man-days

    # Try to use a "1" to size things, if we have it
    ones = [x for x in jiradata if isclose( storyPointFloat(x["Story Points"]), 1.0 ) and x["Issue Type"] == "Story"]
    if( len(ones) > 0 ):
        cycletimes = [int(issue["Cycle Time(Days)"]) for issue in ones]
        cycleTimeOfOneSmallThing = median( cycletimes )
    else:
        # use bugs
        bugs = [x for x in jiradata if x["Issue Type"] == "Bug"]
        if( len(bugs) > 0 ):
            cycletimes = [int(issue["Cycle Time(Days)"]) for issue in bugs]
            cycleTimeOfOneSmallThing = median( cycletimes )

    # The Size of an object is roughly the
    for issue in jiradata:
        issue["Size"] = round( int(issue["Cycle Time(Days)"]) / cycleTimeOfOneSmallThing, 0 )
        if( issue["Size"] == 0 ):
            issue["Size"] = 1.0 #Everything must be at least one small things

def computeAvgThroughput( jiradata, options ):
    sizes = [issue["Size"] for issue in jiradata]
    throughput = int( round( sum( sizes ) / int(options.prevsprints), 0 ) )
    return throughput

if __name__ == '__main__':
    options = parseOptions()
    jiradata, backlogdata = readData( options )

    jiradata = onlyJirasWithInProgressDate( jiradata )

    addSizeToAllIssues( jiradata )

    lives, bugs, stories = splitIssues( jiradata )

    metadata = dict()
    metadata["lives"] = getMetaData( lives )
    metadata["bugs"] = getMetaData( bugs )
    metadata["stories"] = getMetaData( stories )

    metadata["throughput"] = computeAvgThroughput( jiradata, options )
    print( metadata["throughput"])
    allruns = []
    for run in range( 0, int(options.runs)):
        runResult = doRun( backlogdata, options, metadata )
        allruns.append( runResult )

    finalStats = computeStats( backlogdata, allruns, options )

    print( finalStats )
