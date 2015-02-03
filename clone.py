from jira.client import JIRA
import sys, json
from cred import *
from config import *


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
    ap.add_argument('-v', dest='verbose',
                    action='store_true',
                    default=False)

    return ap.parse_args()


def pseudoclone4external():
    return src_project in external_projects


if __name__ == '__main__':

    args = parse_args()
    print args

    jira_client = JIRA(options={'server': server}, basic_auth=(user, passwd))
    src_issue = jira_client.issue(args.task_key)
    if args.verbose:
        from pprint import pprint

        print "The source issue:\n[%s] %s" % (src_issue.key, src_issue.fields().summary)

    src_project = src_issue.fields().project.key
    src_summary = src_issue.fields().summary
    src_key = src_issue.key
    src_prio_name = src_issue.fields().priority.name
    asignee_name = args.assignee if args.assignee else src_issue.fields().assignee.name

    if pseudoclone4external():
        project = external_projects[src_project]
        taskType = EXTERNAL_TASK_TYPE
        print "Creating an internal counterpart for the external ticket"
    else:
        project = src_project
        taskType = src_issue.fields().customfield_10049.value
    wo = None

    if pseudoclone4external():
        topTask = None
    else:
        if src_issue.fields().issuetype.name == 'Sub-task':
            topTask = src_issue.fields().parent.key
            if src_issue.fields().customfield_11311:
                wo = src_issue.fields().customfield_11311.value
        else:
            topTask = src_key

    if not wo:
        if pseudoclone4external():
            wo = EXTERNAL_WO
        else:
            wo = src_issue.fields().customfield_11311.value

    for version in args.fix_version:

        print "Creating task for", version

        versionPrefix = '.'.join(version.split('.')[:2])

        if pseudoclone4external():
            summary = '%s: %s' % (src_key, src_summary)
            if args.verbose:
                print summary
            description = src_issue.fields().description
            issue_type = 'Bug'

        else:
            summary = 'CLONE %s: %s' % (versionPrefix, src_summary)
            description = '%s clone. Please see %s for details' % (versionPrefix, src_key)
            issue_type = 'Sub-task'

        issue_dict = {'project': {'key': project},
                      'summary': summary,
                      'description': description,
                      'issuetype': {'name': issue_type},
                      CustomFields.TASK_TYPE: {'value': taskType},
                      'priority': {'name': src_prio_name},
                      'parent': {'key': topTask},
                      'assignee': {'name': asignee_name},
                      'fixVersions': [{'name': version}]}
        if pseudoclone4external():
            # todo: should we support many?
            # todo: definitely add code to derive the actual version (if possible... perhaps configuration)
            ext_version = src_issue.fields().versions[0].name
            if ext_version.count('.') == 2:
                ext_version += ".1"
            issue_dict['versions'] = [{'name': ext_version}]


        if wo:
            issue_dict[CustomFields.WO] = {'value': wo}
        else:
            print "Warning! No WorkOrder value set in", args.task_key

        if args.dry_run:
            print "dry run mode, created issue would have the following fields"
            from pprint import pprint

            pprint(issue_dict)
        else:
            r = jira_client.create_issue(fields=issue_dict)
            if not pseudoclone4external():
                r.fields.labels.append('clone')
                r.update(fields={"labels": r.fields.labels})
            print "Created:", r.key
            jira_client.create_issue_link(type='relates to', inwardIssue=r.key, outwardIssue=src_key)
            print "Linked %s with %s" % (r.key, src_key)

