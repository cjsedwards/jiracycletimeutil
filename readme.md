The scripts here help to query data from JIRA REST API and parse it into a useful CSV file.

The primary use case I was trying to solve was to calculate cycle times. The start/end date of an issue was not trivial to get, and I had to use the changelog to obtain this information.

Usage:
python3 queryJira.py --user=USERNAME --password=PASSWORD --jira=https://YOURJIRAURL --query="JQL QUERY HERE" | python JSONtoPSV.py > psvout.txt
