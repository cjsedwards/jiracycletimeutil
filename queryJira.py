import requests
import optparse

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

    payload = {"jql":options.query, "expand":"changelog"}

    r = requests.get( options.jira_url + '/rest/api/2/search', params=payload, auth=(options.user, options.password) )

    print (r.text)
