import requests
import optparse
import json

if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-u', '--user', dest='user', help='Username to access JIRA')
    parser.add_option('-p', '--password', dest='password', help='Password to access JIRA')
    parser.add_option('-j', '--jira', dest='jira_url', help='JIRA Base URL, ex: https://jira.atlassian.com')
    parser.add_option('-q', '--query', dest='query', help='JQL Query')

    (options, args) = parser.parse_args()

    if( not options.user or not options.password or not options.jira_url or not options.query):
        parser.print_help()
        exit()

    results = []

    count = 0
    while True:
        payload = {"jql":options.query, "expand":"changelog", "startAt":str(count)}

        r = requests.get( options.jira_url + '/rest/api/2/search', params=payload, auth=(options.user, options.password) )

        parsed = json.loads(r.text)
        total = int(parsed["total"])
        maxResults = int(parsed["maxResults"])

        results.append(parsed)

        count += maxResults
        if (count >= total):
            break

    print(json.dumps(results))
