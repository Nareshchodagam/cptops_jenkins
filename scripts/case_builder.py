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
import traceback
import shlex

def json_imports():
    '''
    Imports case_presets.json
    '''
    presets = "/home/jenkins/git/cptops_jenkins_jobs/scripts/case_presets.json"
    with open(presets, 'r') as pre:
        sets = json.load(pre)
    return sets

def hostlist_builder():
    create_cmd = "python /home/jenkins/git/cptops_case_gen/bin/create_cases.py -d "
    dc_list = 'asg,sjl,chi,was,dfw,phx,lon,frf,tyo'
    os.chdir('/home/jenkins/git/cptops_case_gen/hostlists/')
    case_cmd = create_cmd + dc_list
    logging.debug(case_cmd)
    logging.debug('Building updated POD list.....')
    retcode = subprocess.check_call(shlex.split(case_cmd))
    if retcode != 0:
        logging.error('POD list creation failed')
        sys.exit(1)

def pod_builder(sets):
    '''
    Function that extracts information from case_presets.json. Builds the
    pod_cases.py command string.
    '''
    pod_cmd = "/home/jenkins/git/cptops_case_gen/bin/gen_cases.py"
    case_file = '/home/jenkins/git/cases.sh'
    bundle = os.environ['BUNDLE']
    role_class = os.environ['ROLE_CLASS'].lower()
    role_status = role_class.split('_')[-1].upper()
    dr = "True" if role_status == "DR" else "FALSE"
    sub_title = os.environ['SUBJECT']
    group_file = "/home/jenkins/hostlist/PODGROUP" if os.environ['PODGROUP'] != "" else "/home/jenkins/git/cptops_case_gen/hostlists/" + sets[role_class][role_status]['PODGROUP']
    gsize = os.environ['GROUPSIZE'] if os.environ['GROUPSIZE'] != "DEFAULT" else sets[role_class][role_status]['GROUPSIZE']
    tagsize = os.environ['TAGGROUPS'] if os.environ['TAGGROUPS'] != "DEFAULT" else sets[role_class][role_status]['TAGGROUPS']
    infra_type = sets[role_class][role_status]['INFRA']
    role = sets[role_class][role_status]['ROLE']
    template = sets[role_class][role_status]['TEMPLATEID']

    logging.debug("TEMPLATEID = " + template)
    logging.debug("GROUPSIZE = " + str(gsize))
    logging.debug("TAGGROUPS = " + str(tagsize))
    logging.debug("INFRA = " + infra_type)
    logging.debug("ROLE = " + role)
    logging.debug("SUBJECT = " + sub_title)
    logging.debug("PODGROUP = " + group_file)
    logging.debug("Contents of uploaded file %s" %  os.environ['PODGROUP'])
    with open(group_file, 'r') as fin:
        print fin.read()

    if not os.environ['FILTER']:
        case_cmd = "python %s -p %s -r %s -t %s -b %s -d %s -s %s --patchset %s --taggroups %s  --infra %s" \
             % (pod_cmd, group_file, role, template, bundle, dr.title(), gsize, bundle, tagsize, infra_type)
        if sub_title:
            case_cmd = case_cmd + " -g " + sub_title
        logging.debug(case_cmd)
        file_proc = subprocess.Popen(shlex.split(case_cmd), stdout=subprocess.PIPE)
        with open(case_file, 'w') as cases:
            cases.write(file_proc.stdout.read())
    else:
        case_cmd = "python %s -p %s -r %s -t %s -b %s -d %s -s %s -f %s --patchset %s --taggroups %s  --infra %s" \
             % (pod_cmd, group_file, role, template, bundle, dr.title(), gsize, os.environ['FILTER'], bundle, tagsize, infra_type)
        if sub_title:
            case_cmd = case_cmd + " -g " + sub_title
        logging.debug("FILTER = " + os.environ['FILTER'])
        logging.debug(case_cmd)
        file_proc = subprocess.Popen(shlex.split(case_cmd), stdout=subprocess.PIPE)
        with open(case_file, 'w') as cases:
                cases.write(file_proc.stdout.read())

def case_executor():
    '''
    Functions that loops thru cases.sh to create implementation plans and
    gus cases. Gus_cases.py requires proxy setting while build_plan.py
    does not require proxy setting. Hence the loop.
    '''
    case_file = '/home/jenkins/git/cases.sh'
    cmd_type = re.compile(r'^(python\s[a-z_.]*)')
    pods = re.compile(r'--inst\s([A-Za-z0-99,]*)')
    os.chdir('/home/jenkins/git/cptops_case_gen/bin')
    failed_plans = []

    if os.path.isfile(case_file):
        with open(case_file, 'r') as cases:
            for line in cases:
                ln_check = cmd_type.match(line)
                if ln_check.group() == "python gus_cases_vault.py":
                    os.environ['https_proxy'] = "http://public-proxy1-0-sfm.data.sfdc.net:8080/"
                    logging.debug(line)
                    retcode = os.system(line)
                    logging.debug(retcode)
                    if retcode != 0:
                        pods_match = pods.findall(line)
                        logging.debug(pods_match)
                        failed_plans.append(pods_match)
                else:
                    os.environ['https_proxy'] = ""
                    logging.debug(line)
                    retcode = os.system(line)
                    logging.debug(retcode)
                    if retcode != 0:
                      logging.debug(line)
    else:
        logging.debug("cases.sh file not found!")
        sys.exit(1)
    return failed_plans

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    sets = json_imports()
    if os.environ['PODGROUP'] == "":
        hostlist_builder()
    pod_builder(sets)
    failures = case_executor()
    if failures:
        for fail in failures:
            logging.debug(str(fail) + " failed to generate implementation plans.")
        sys.exit(1)