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

def cmd_builder(sets):
    '''
    Function that builds the gen_cases.py build command. It gathers options from
    the case_presets and builds the command.
    '''
    role_class = os.environ['ROLE_CLASS'].lower()
    role_status = role_class.split('_')[-1].upper()
    #dr = "True" if role_status == "DR" else "FALSE"
    pod_cmd = ["python", "/home/jenkins/git/cptops_case_gen/bin/gen_cases.py" ]
    bld_cmd = {}
    bld_cmd['status'] = "True" if role_status == "DR" else "FALSE"
    bld_cmd['bundle'] = os.environ['BUNDLE']
    bld_cmd['patchset'] = os.environ['BUNDLE']
    bld_cmd['podgroup'] = "/home/jenkins/hostlist/PODGROUP" if os.environ['PODGROUP'] != "" else "/home/jenkins/git/cptops_case_gen/hostlists/" + sets[role_class][role_status]['PODGROUP']
    bld_cmd['gsize'] = os.environ['GROUPSIZE'] if os.environ['GROUPSIZE'] != "DEFAULT" else sets[role_class][role_status]['GROUPSIZE']
    bld_cmd['tagsize'] = os.environ['TAGGROUPS'] if os.environ['TAGGROUPS'] != "DEFAULT" else sets[role_class][role_status]['TAGGROUPS']
    bld_cmd['infra'] = sets[role_class][role_status]['INFRA']
    bld_cmd['role'] = sets[role_class][role_status]['ROLE']
    bld_cmd['template'] = sets[role_class][role_status]['TEMPLATEID']
    bld_cmd['regexfilter'] = os.environ['REGEX']
    bld_cmd['filter'] = os.environ['FILTER']
    bld_cmd['subject'] = os.environ['SUBJECT']

    logging.debug("TEMPLATEID = " + bld_cmd['template'])
    logging.debug("GROUPSIZE = " + str(bld_cmd['gsize']))
    logging.debug("TAGGROUPS = " + str(bld_cmd['tagsize']))
    logging.debug("INFRA = " + bld_cmd['infra'])
    logging.debug("ROLE = " + bld_cmd['role'])
    logging.debug("SUBJECT = " + bld_cmd['subject'])
    logging.debug("PODGROUP = " + bld_cmd['podgroup'])
    logging.debug("REGEXFILTER = " + bld_cmd['regexfilter'])
    logging.debug("Contents of uploaded file %s" %  os.environ['PODGROUP'])
    with open(bld_cmd['podgroup'], 'r') as fin:
        print fin.read()
    pod_builder(bld_cmd)

def pod_builder(bld_cmd):
    '''
    Function that extracts information from case_presets.json. Builds the
    pod_cases.py command string.
    '''
    case_file = '/home/jenkins/git/cases.sh'
    opt_dict = {'gsize': '-s',
                'role': '-r',
                'podgroup': '-p',
                'template': '-t',
                'status': '-d',
                'bundle': '-b',
                'patchset': '--patchset',
                'tagsize': '--taggroups',
                'infra': '--infra',
                'gsize': '-s',
                'filter': '-f',
                'regexfilter': '--regexfilter' }
    pod_cmd = ["python", "/home/jenkins/git/cptops_case_gen/bin/gen_cases.py" ]
    for opt in opt_dict.iterkeys():
        if bld_cmd.has_key(opt) and bld_cmd[opt] != "":
            pod_cmd.append(opt_dict[opt])
            pod_cmd.append(str(bld_cmd[opt]))
    logging.debug(pod_cmd)
    file_proc = subprocess.Popen(pod_cmd, stdout=subprocess.PIPE)
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
    cmd_builder(sets)
    failures = case_executor()
    if failures:
        for fail in failures:
            logging.debug(str(fail) + " failed to generate implementation plans.")
        sys.exit(1)