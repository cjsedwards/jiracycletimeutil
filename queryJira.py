import requests
import optparse
import json

if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-u', '--user', dest='user', default="", help='Username to access JIRA')
    parser.add_option('-p', '--password', dest='password', default="", help='Password to access JIRA')
    parser.add_option('-j', '--jira', dest='jira_url', default="", help='JIRA Base URL, ex: https://jira.atlassian.com')
    parser.add_option('-q', '--query', dest='query', default="", help='JQL Query')

    (options, args) = parser.parse_args()

    if(options.user == "" or options.password == "" or options.jira_url == "" or options.query == ""):
        parser.print_help()
        exit()

    payload = {"jql":options.query, "expand":"changelog"}

    r = requests.get( options.jira_url + '/rest/api/2/search', params=payload, auth=(options.user, options.password) )

    parsed = json.loads(r.text)

    print(json.dumps(parsed, indent=4, sort_keys=True))
