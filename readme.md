The scripts here help to query data from JIRA REST API and parse it into a useful CSV file.

**Cycle Time**

The primary use case I was trying to solve was to calculate cycle times. The start/end date of an issue was not trivial to get, and I had to use the changelog to obtain this information.

**Actual Days in Progress**

Takes into account when Jira issue moves is moved back into 'Open' state and than 'In Progress' at later point.

**Usage**
Querying Data from Jira:
```
python3 queryJira.py --user=USERNAME --password=PASSWORD --jira=https://YOURJIRAURL --query="JQL QUERY HERE" | python JSONtoPSV.py > psvout.txt
```

Forecast Generator:
```
python3 forecastGenerator.py --jiradata=PATH_TO_JIRA_EXPORT --backlog=sampleBacklog.psv --wiplimit=4 --runs=1000 --sprints=5
```

**Required Packages**

[Python3] (https://www.python.org/)

[requests] (http://docs.python-requests.org/en/master/user/install/)

[NumPy] (http://www.numpy.org/)
