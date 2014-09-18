from jira.client import JIRA
import sys, json
from cred import *


def parse_args():
    from argparse import ArgumentParser
    ap = ArgumentParser(description='JIRA tools for anonymous project')
    ap.add_argument('task_key',
                    action='store')
    # nargs '+' make append unnecessary if not wrong (we do not need a list of lists here...)
    ap.add_argument('fix_version',
                    action='store',
                    nargs='+')
    ap.add_argument('-a', dest='assignee',
                    action='store',
                    help='The assignee of created tickets, if different from that of the source ticket',
                    default=None)
    ap.add_argument('-d', dest='dry_run',
                    action='store_true',
                    default=False)

    return ap.parse_args()

if __name__ == '__main__':

    args = parse_args()
    print args

    jira_client = JIRA(options={'server': server}, basic_auth=(user, passwd))
    parent = jira_client.issue(args.task_key)
    project = parent.fields().project.key
    parentSummary = parent.fields().summary
    parentKey = parent.key
    parentPrioName = parent.fields().priority.name
    asignee_name = args.assignee if args.assignee else parent.fields().assignee.name
    taskType = parent.fields().customfield_10049.value
    wo = parent.fields().customfield_11311.value if parent.fields().customfield_11311 else None
    if parent.fields().issuetype.name == 'Sub-task':
        topTask = parent.fields().parent.key
    else:
        topTask = parentKey

    for version in args.fix_version:

        print "Creating task for", version

        versionPrefix = '.'.join(version.split('.')[:2])

        issue_dict = {'project': {'key': project},
                      'summary': 'CLONE %s: %s' % (versionPrefix, parentSummary),
                      'description': '%s clone. Please see %s for details' % (versionPrefix, parentKey),
                      'issuetype': {'name': 'Sub-task'},
                      'customfield_10049': {'value': taskType},
                      'priority': {'name': parentPrioName},
                      'parent': {'key': topTask},
                      'assignee': {'name': asignee_name},
                      'fixVersions': [{'name': version}],

        }
        if wo:
            issue_dict['customfield_11311'] = {'value': wo}
        else:
            print "Warning! No WorkOrder value set in", args.task_key

        if args.dry_run:
            print "dry run mode, created issue would have the following fields\n", issue_dict
        else:
            r = jira_client.create_issue(fields=issue_dict)
            r.fields.labels.append('clone')
            r.update(fields={"labels": r.fields.labels})
            print "Created:", r.key

