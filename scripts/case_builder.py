#!/usr/bin/python
#
#
'''
    Jenkins Python script to create implementation plans and create cases.
'''

import json
import subprocess
from subprocess import PIPE, Popen
import os
import re
import sys
import logging

def json_imports():
    presets = "/home/jenkins/git/cptops_jenkins_jobs/scripts/case_presets.json"
    with open(presets, 'r') as pre:
        sets = json.load(pre)
    return sets

def pod_builder(sets):
    pod_cmd = "/home/jenkins/git/cptops_case_gen/bin/pods_cases.py"
    role_class = os.environ['ROLE_CLASS'].lower()
    bundle = os.environ['BUNDLE']
    dr = os.environ['DR']
    month_Dict = {'01':'Jan', '02':'Feb', '03':'Mar', '04':'Apr', '05':'May', '06':'Jun', \
                 '07':'Jul', '08':'Aug', '09':'Sep', '10':'Oct', '11':'Nov', '12':'Dec'}
    mon = month_Dict[bundle.split('.')[1]]

    if os.environ['DR'] == "false":
        status = "Prod"
    else:
        status = "DR"

    if os.environ['CANARY'] == "false":
        group_file = sets[role_class][status]['PODGROUP']
        template = sets[role_class][status]['TEMPLATEID']
        gsize = sets[role_class][status]['GROUPSIZE']
        tagsize = sets[role_class][status]['TAGGROUPS']
        role = sets[role_class][status]['ROLE']

        logging.debug(group_file)
        logging.debug(template)
        logging.debug(gsize)
        logging.debug(tagsize)
        logging.debug(role)
        logging.debug(dr)

        if not os.environ['FILTER']:
            case_cmd = "python %s -p /home/jenkins/git/cptops_case_gen/hostlists/%s -r %s -t %s -b %s -d %s -s %d -g \"%s\" --patchset %s --taggroups %d" \
                 % (pod_cmd, group_file, role, template, mon.lower(), dr.title(), gsize, status, bundle, tagsize)
            logging.debug(case_cmd)
            file_proc = subprocess.Popen(case_cmd.split(), stdout=subprocess.PIPE)
            with open("cases.sh", 'w') as cases:
                cases.write(file_proc.stdout.read())
        else:
            case_cmd = "python %s -p /home/jenkins/git/cptops_case_gen/hostlists/%s -r %s -t %s -b %s -d %s -s %d -g \"%s\" -f %s --patchset %s --taggroups %d" \
                 % (pod_cmd, group_file, role, template, mon.lower(), dr.title(), gsize, status, os.environ['FILTER'], bundle, tagsize)
            logging.debug(os.environ['FILTER'])
            logging.debug(case_cmd)
            file_proc = subprocess.Popen(case_cmd.split(), stdout=subprocess.PIPE)
            with open("cases.sh", 'w') as cases:
                cases.write(file_proc.stdout.read())
    else:
        group_file = sets[role_class]['CANARY'][status]['PODGROUP']
        template = sets[role_class]['CANARY'][status]['TEMPLATEID']
        gsize = sets[role_class]['CANARY'][status]['GROUPSIZE']
        tagsize = sets[role_class]['CANARY'][status]['TAGGROUPS']
        role = sets[role_class]['CANARY'][status]['ROLE']

        logging.debug(group_file)
        logging.debug(template)
        logging.debug(gsize)
        logging.debug(tagsize)
        logging.debug(role)
        logging.debug(dr)

        if not os.environ['FILTER']:
            case_cmd = "python %s -p /home/jenkins/git/cptops_case_gen/hostlists/%s -r %s -t %s -b %s -d %s -s %d -g \"%s\" --patchset %s --taggroups %d" \
                 % (pod_cmd, group_file, role, template, mon.lower(), dr.title(), gsize, status, bundle, tagsize)
            logging.debug(case_cmd)
            file_proc = subprocess.Popen(case_cmd.split(), stdout=subprocess.PIPE)
            with open("cases.sh", 'w') as cases:
                cases.write(file_proc.stdout.read())
        else:
            case_cmd = "python %s -p /home/jenkins/git/cptops_case_gen/hostlists/%s -r %s -t %s -b %s -d %s -s %d -g \"%s\" -f %s --patchset %s --taggroups %d" \
                  % (pod_cmd, group_file, role, template, mon.lower(), dr.title(), gsize, status, os.environ['FILTER'], bundle, tagsize)
            logging.debug(os.environ['FILTER'])
            logging.debug(case_cmd)
            file_proc = subprocess.Popen(case_cmd.split(), stdout=subprocess.PIPE)
            with open("cases.sh", 'w') as cases:
                cases.write(file_proc.stdout.read())

def case_executor():
    case_file = '/home/jenkins/git/cases.sh'
    cmd_type = re.compile(r'^(python\s[a-z_.]*)')
    os.chdir('/home/jenkins/git/cptops_case_gen/bin')

    if os.path.isfile(case_file):
        with open(case_file, 'r') as cases:
            for line in cases:
                ln_check = cmd_type.match(line)
                if ln_check.group() == "python gus_cases.py":
                    os.environ['https_proxy'] = "http://public-proxy1-0-sfm.data.sfdc.net:8080/"
                    logging.debug(line)
                    retcode = subprocess.call(line.split())
                    logging.debug(retcode)
                    if retcode != 0:
                      sys.exit(1)
                else:
                    os.environ['https_proxy'] = ""
                    logging.debug(line)
                    retcode = subprocess.call(line.split())
                    logging.debug(retcode)
                    if retcode != 0:
                      sys.exit(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    sets = json_imports()
    pod_builder(sets)
    case_executor()