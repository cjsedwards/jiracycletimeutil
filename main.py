import requests
import optparse
import json

if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-u', '--user', dest='user', default="", help='Username to access JIRA')
    parser.add_option('-p', '--password', dest='password', default="", help='Password to access JIRA')
    parser.add_option('-j', '--jira', dest='jira_url', default="", help='JIRA Base URL, ex: https://jira.atlassian.com')
    parser.add_option('-i', '--issue', dest='issue', default="", help='JIRA Issue, ex: DEV-2814')

    (options, args) = parser.parse_args()

    if(options.user == "" or options.password == "" or options.jira_url == ""):
        parser.print_help()
        exit()

    r = requests.get( options.jira_url + '/rest/api/latest/issue/' + options.issue + "?expand=changelog", auth=(options.user, options.password) )

    parsed = json.loads(r.text)

    print(json.dumps(parsed, indent=4, sort_keys=True))
