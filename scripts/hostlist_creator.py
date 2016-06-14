#!/usr/bin/python
#
'''
Creates hostlist via create_cases.py script. Program creates a update branch,
runs the create_cases program and then creates PR to the master. It can also
auto-merge the pull requests. 
'''
import os
import requests
import sys
import subprocess
import shlex


def create_hostlist():
    _wrkspc = os.environ['WORKSPACE']
    os.environ['HOME'] = _wrkspc
    os.environ['PYTHONPATH'] = _wrkspc + "/git/cptops_case_gen/idbhost/includes"
    cmd = "python " + _wrkspc + "/git/cptops_case_gen/bin/create_cases.py "
    git_add = 'git add .'
    git_commit = 'git commit -m "Jenkins Automated Hostlist builder"'
    os.chdir( _wrkspc + "/git/cptops_case_gen/hostlists")
    opt_dict = {"pod": "all",
                "afw": "all",
                "DATA_RESTORE": "all",
                "hammer": "all",
                "mta": "all" }
    for key,val in opt_dict.iteritems():
        retcode = subprocess.check_call(shlex.split(cmd + "-t %s -d %s" % (key, val)))
        if retcode != 0:
            print "Failed to create %s hostlist." % (key)
            sys.exit(1)
    for git in git_add,git_commit:
        retcode = subprocess.check_call(shlex.split("%s" % (git)))
        if retcode !=0 :
            print "Failed to commit new files."
            sys.exit(1)

if __name__ == "__main__":
    create_hostlist()