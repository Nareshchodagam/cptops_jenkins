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

def json_imports():
    '''
    Imports case_presets.json
    '''
    presets = "/home/jenkins/git/cptops_jenkins_jobs/scripts/case_presets.json"
    with open(presets, 'r') as pre:
        sets = json.load(pre)
    return sets

def pod_builder(sets):
    '''
    Function that extracts information from case_presets.json. Builds the 
    pod_cases.py command string. 
    '''
    pod_cmd = "/home/jenkins/git/cptops_case_gen/bin/pods_cases.py"
    case_file = '/home/jenkins/git/cases.sh'
    month_Dict = {'01':'Jan', '02':'Feb', '03':'Mar', '04':'Apr', '05':'May', '06':'Jun', \
         '07':'Jul', '08':'Aug', '09':'Sep', '10':'Oct', '11':'Nov', '12':'Dec'}
    bundle = os.environ['BUNDLE']
    mon = month_Dict[bundle.split('.')[1]]
    role_class = os.environ['ROLE_CLASS'].lower()
    role_status = role_class.split('_')[-1].upper()
    dr = "True" if role_status == "DR" else "FALSE"    
    group_file = os.environ['PODGROUP'] if os.environ['PODGROUP'] != "DEFAULT" else sets[role_class][role_status]['PODGROUP']    
    gsize = os.environ['GROUPSIZE'] if os.environ['GROUPSIZE'] != "DEFAULT" else sets[role_class][role_status]['GROUPSIZE']
    tagsize = os.environ['TAGGROUPS'] if os.environ['TAGGROUPS'] != "DEFAULT" else sets[role_class][role_status]['TAGGROUPS']
    role = sets[role_class][role_status]['ROLE']
    template = sets[role_class][role_status]['TEMPLATEID']
    
    logging.debug("PODGROUP = " + group_file)
    logging.debug("TEMPLATEID = " + template)
    logging.debug("GROUPSIZE = " + str(gsize))
    logging.debug("TAGGROUPS = " + str(tagsize))
    logging.debug("ROLE = " + role)

    if not os.environ['FILTER']:
        case_cmd = "python %s -p /home/jenkins/git/cptops_case_gen/hostlists/%s -r %s -t %s -b %s -d %s -s %s -g \"%s\" --patchset %s --taggroups %s" \
             % (pod_cmd, group_file, role, template, mon.lower(), dr.title(), gsize, role_status, bundle, tagsize)
        logging.debug(case_cmd)
        file_proc = subprocess.Popen(case_cmd.split(), stdout=subprocess.PIPE)
        with open(case_file, 'w') as cases:
            cases.write(file_proc.stdout.read())
    else:
        case_cmd = "python %s -p /home/jenkins/git/cptops_case_gen/hostlists/%s -r %s -t %s -b %s -d %s -s %s -g \"%s\" -f %s --patchset %s --taggroups %s" \
             % (pod_cmd, group_file, role, template, mon.lower(), dr.title(), gsize, role_status, os.environ['FILTER'], bundle, tagsize)
        logging.debug("FILTER = " + os.environ['FILTER'])
        logging.debug(case_cmd)
        file_proc = subprocess.Popen(case_cmd.split(), stdout=subprocess.PIPE)
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
                      logging.debug(line)
                      sys.exit(1)
                else:
                    os.environ['https_proxy'] = ""
                    logging.debug(line)
                    retcode = subprocess.call(line.split())
                    logging.debug(retcode)
                    if retcode != 0:
                      logging.debug(line)
                      sys.exit(1)
    else:
        logging.debug("cases.sh file not found!")
        sys.exit(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    sets = json_imports()
    pod_builder(sets)
    #case_executor()