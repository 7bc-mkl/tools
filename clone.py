from jira.client import JIRA
import sys,json
from cred import *



if len(sys.argv) < 3:
    print "Usage:"
    print "\t clone.py task_key fix_version_1 [fix_version_2] [fix_version_3] ..."

j = JIRA(options = {'server':server},basic_auth=(user, passwd))
parent = j.issue(sys.argv[1])
project =  parent.fields().project.key
parentSummary=parent.fields().summary
parentKey=parent.key
parentPrioName=parent.fields().priority.name
parentAssignee=parent.fields().assignee.name
taskType=parent.fields().customfield_10049.value
wo=parent.fields().customfield_11311.value
if parent.fields().issuetype.name=='Sub-task':
    topTask=parent.fields().parent.key
else:
    topTask=parentKey

for el in sys.argv[2:]:

    print "Creating task for", el

    versionPrefix='.'.join(el.split('.')[:2])
    
    issue_dict = {'project': {'key': project},
     'summary': 'CLONE %s: %s'%(versionPrefix,parentSummary),
     'description': '%s clone. Please see %s for details'%(versionPrefix, parentKey),
     'issuetype': {'name': 'Sub-task'},
     'customfield_10049' : {'value':taskType},
     'priority': {'name':parentPrioName},
     'parent' : {'key':topTask},
     'assignee' : {'name': parentAssignee},
     'fixVersions' : [{'name': el}],
     'customfield_11311' : {'value':wo}
    }



    #print  issue_dict
    r = j.create_issue(fields=issue_dict)
    r=r.fields.labels.append('clone')
    print "Created:", r.key

