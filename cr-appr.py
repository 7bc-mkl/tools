from collections import OrderedDict
from jira.client import JIRA

from cred import *
from config import *


def add_exclude(ap, type_str):
    ap.add_argument('--exclude-' + type_str, dest='excluded_types',
                    action='append_const',
                    const=type_str,
                    help='Do not create %s sub-task' % (type_str.upper(),),
                    default=None)


def parse_args():
    from argparse import ArgumentParser

    ap = ArgumentParser(description='JIRA subtask creation for anonymous project')
    ap.add_argument('task_key',
                    action='store')
    add_exclude(ap, SubtaskType.ba)
    add_exclude(ap, SubtaskType.ta)
    ap.add_argument('-d', dest='dry_run',
                    action='store_true',
                    help='dry run',
                    default=False)

    args = ap.parse_args()
    if not args.excluded_types:
        args.excluded_types = {}
    return args


if __name__ == '__main__':
    j = JIRA(options={'server': server}, basic_auth=(user, passwd))

    args = parse_args()

    parent = j.issue(args.task_key)
    project = parent.fields().project.key
    parentKey = parent.key
    parentSummary = parent.fields().summary
    parentPrioName = parent.fields().priority.name
    extId = parent.fields().customfield_10034
    wo = parent.fields().customfield_11311.value if parent.fields().customfield_11311 else None
    if not default_assignees.get(project):
        raise ValueError('No config for project ' + project)
    if not wo:
        raise ValueError('No WO set in ' + parentKey)
    # todo: a common "starting point" dict for all of them?
    ba_issue_dict = {'project': {'key': project},
                     'summary': '[BA] ' + parentSummary,
                     'description': 'Functional documentation update.',
                     'issuetype': {'name': 'Sub-task'},
                     CustomFields.TASK_TYPE: {'value': baType},
                     'priority': {'name': parentPrioName},
                     CustomFields.EXTERNAL_ID: extId,
                     'parent': {'key': parentKey},
                     CustomFields.WO: {'value': wo},
                     'assignee': {'name': (default_assignees[project][SubtaskType.ba])}
    }

    ta_issue_dict = {'project': {'key': project},
                     'summary': '[TA] ' + parentSummary,
                     'description': 'Technical documentation update (if needed) and development guidance.',
                     'issuetype': {'name': 'Sub-task'},
                     CustomFields.TASK_TYPE: {'value': taType},
                     'priority': {'name': parentPrioName},
                     CustomFields.EXTERNAL_ID: extId,
                     'parent': {'key': parentKey},
                     CustomFields.WO: {'value': wo},
                     'assignee': {'name': (default_assignees[project][SubtaskType.ta])}

    }

    dev_issue_dict = {'project': {'key': project},
                      'summary': '[DEV] ' + parentSummary,
                      'description': 'Implementation of the change.',
                      'issuetype': {'name': 'Sub-task'},
                      CustomFields.TASK_TYPE: {'value': devType},
                      'priority': {'name': parentPrioName},
                      CustomFields.EXTERNAL_ID: extId,
                      'parent': {'key': parentKey},
                      CustomFields.WO: {'value': wo},
                      'assignee': {'name': (default_assignees[project][SubtaskType.dev])}
    }

    qa_issue_dict = {'project': {'key': project},
                     'summary': '[QA] ' + parentSummary,
                     'description': 'Test cases update and test execution.',
                     'issuetype': {'name': 'Sub-task'},
                     CustomFields.TASK_TYPE: {'value': qaType},
                     'priority': {'name': parentPrioName},
                     CustomFields.EXTERNAL_ID: extId,
                     'parent': {'key': parentKey},
                     CustomFields.WO: {'value': wo},
                     'assignee': {'name': (default_assignees[project][SubtaskType.qa])}
    }

    issue_dict = OrderedDict((
        (SubtaskType.ba, ba_issue_dict),
        (SubtaskType.ta, ta_issue_dict),
        (SubtaskType.dev, dev_issue_dict),
        (SubtaskType.qa, qa_issue_dict))
    )

    for sub_dict_key in issue_dict.keys():
        if sub_dict_key in args.excluded_types:
            print "Skipping", sub_dict_key
        else:
            if args.dry_run:
                print "dry run mode, created issue would have the following fields\n", issue_dict[sub_dict_key]
            else:
                r = j.create_issue(fields=issue_dict[sub_dict_key])
                print r

