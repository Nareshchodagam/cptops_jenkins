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
import shlex
import argparse
import case_opts as co
import pprint


def json_imports():
    '''
    Imports case_presets.json
    '''
    presets = os.environ["HOME"] + "/git/cptops_jenkins/scripts/case_presets.json"
    with open(presets, 'r') as pre:
        sets = json.load(pre)
    return sets


def cmd_builder(sets, r_class=False):
    '''
    Function that builds the gen_cases.py build command. It gathers options from
    the case_presets and builds the command.
    '''
    home_dir = os.environ["HOME"]
    if options.canary:
        role_class = r_class
    else:
        role_class = options.roleclass
    role_status = role_class.split('_')[-1].upper()
    #dr = "True" if role_status == "DR" else "FALSE"
    pod_cmd = ["python", home_dir + "/git/cptops_case_gen/gen_cases.py" ]
    bld_cmd = {}
    bld_cmd['status'] = "True" if role_status == "DR" else "FALSE"
    bld_cmd['patchset'] = options.bundle
    bld_cmd['podgroup'] = options.podgroup if options.podgroup != None else home_dir + "/git/cptops_case_gen/hostlists/" + sets[role_class][role_status]['PODGROUP']
    bld_cmd['gsize'] = options.groupsize if options.groupsize != None else sets[role_class][role_status]['GROUPSIZE']
    bld_cmd['tagsize'] = options.taggroups if options.taggroups != None else sets[role_class][role_status]['TAGGROUPS']
    bld_cmd['infra'] = sets[role_class][role_status]['INFRA']
    bld_cmd['role'] = sets[role_class][role_status]['ROLE']
    bld_cmd['template'] = sets[role_class][role_status]['TEMPLATEID']

    if options.regex is None:
        if 'REGEX' in sets[role_class][role_status]:
            options.regex = sets[role_class][role_status]['REGEX']
        else:
            options.regex = ""
    if options.filter is None:
        if 'FILTER' in sets[role_class][role_status]:
            length = len(sets[role_class][role_status]['FILTER'])
            #if len(sets[role_class][role_status]['FILTER']) == 1 or len(sets[role_class][role_status]['FILTER']) == 2:
            if length == 1:
                filter = ",".join(sets[role_class][role_status]['FILTER'][0:length])
            else:
                for role_filter in sets[role_class][role_status]['FILTER']:
                    print role_filter
                filter = raw_input("Please select filter from above: ")
        else:
            filter = ""
    bld_cmd['filter'] = filter
    bld_cmd['regexfilter'] = options.regex
    if options.subject == None:
        if options.roleclass in co.req_sub:
            if not options.subject:
                options.subject = raw_input("\nPreset %s requires custom subject.\nPlease add subject line: " % options.roleclass)
        elif options.canary:
            options.subject = "CANARY"
        elif 'SUBJECT' in sets[role_class][role_status].keys():
            options.subject = sets[role_class][role_status]['SUBJECT']
        else:
            options.subject = ""
    bld_cmd['subject'] = options.subject
    bld_cmd['dowork'] = options.dowork
    # This change will help user to choose the way he/she wants to create case.
    if options.host_validation:
        bld_cmd['host_validation'] = options.host_validation
    if options.auto_close_case:
        bld_cmd['auto_close_case'] = options.auto_close_case
    if options.nolinebacker:
        bld_cmd['nolinebacker'] = options.nolinebacker
    #bld_cmd['clusteropstat'] = sets[role_class][role_status]['CL_STATUS']
    #bld_cmd['hostopstat'] = sets[role_class][role_status]['HO_STATUS']

    #Custom parameters within the case_presets.json
    #These options are not within each predefined role_class.
    #So we test if values are present.
    for key in ['CASETYPE', 'IMPL_PLAN' 'EXCLUDES','LIST_FILTER']:
        if key in sets[role_class][role_status]:
            if key == 'EXCLUDES':
                bld_cmd[str.lower(key)] = "hostlists/" + sets[role_class][role_status][key]
            else:
                bld_cmd[str.lower(key)] = sets[role_class][role_status][key]
    if options.cluststat:
       bld_cmd['clusteropstat'] = options.cluststat

    logging.debug("TEMPLATEID = " + bld_cmd['template'])
    logging.debug("GROUPSIZE = " + str(bld_cmd['gsize']))
    logging.debug("TAGGROUPS = " + str(bld_cmd['tagsize']))
    logging.debug("INFRA = " + bld_cmd['infra'])
    logging.debug("ROLE = " + bld_cmd['role'])
    logging.debug("SUBJECT = " + bld_cmd['subject'])
    logging.debug("PODGROUP = " + bld_cmd['podgroup'])
    logging.debug("REGEXFILTER = " + bld_cmd['regexfilter'])
    logging.debug("FILTER = " + bld_cmd['filter'])
    logging.debug("PATCHSET = " + bld_cmd['patchset'])
    logging.debug("Contents of uploaded file %s" %  bld_cmd['podgroup'])
    #logging.debug("CL_STATUS = " + bld_cmd['clusteropstat'])
    #logging.debug("HO_STATUS = " + bld_cmd['hostopstat'])
    with open(bld_cmd['podgroup'], 'r') as fin:
        print fin.read()
    case_builder(bld_cmd)


def initfile():
    with open('cases.sh', 'w') as f:
        f.write('#' * 86 + '\n')
        f.write("#This file is generated by 'CPT case create automation' , please don't edit manually#\n")
        f.write('#' * 86 + '\n')


def case_builder(bld_cmd):
    '''
    Function that extracts information from case_presets.json. Builds the
    pod_cases.py command string.
    '''
    cmd = ''
    case_file = 'cases.sh'
    pod_cmd = ["python", os.environ["HOME"] + "/git/cptops_case_gen/gen_cases.py" ]
    for opt in co.opt_dict.iterkeys():
        if bld_cmd.has_key(opt) and bld_cmd[opt] != "":
            pod_cmd.append(co.opt_dict[opt])
            pod_cmd.append(str(bld_cmd[opt]))
    for item in pod_cmd:
        cmd += str(item)
        cmd += " "
    logging.debug(cmd)
    file_proc = subprocess.Popen(pod_cmd, stdout=subprocess.PIPE)
    with open(case_file, 'a+') as cases:
        cases.write(file_proc.stdout.read())


def case_executor():
    '''
    Functions that loops thru cases.sh to create implementation plans and
    gus cases. Gus_cases.py requires proxy setting while build_plan.py
    does not require proxy setting. Hence the loop.
    '''
    case_file = os.getcwd() + '/cases.sh'
    cmd_type = re.compile(r'^(python\s[a-z_.]*)')
    pods = re.compile(r'--inst\s([A-Za-z0-99,]*)')
    os.chdir(os.environ["HOME"] + '/git/cptops_case_gen')
    failed_plans = []

    if os.path.isfile(case_file):
        with open(case_file, 'r') as cases:
            for line in cases:
                if not line.startswith("#"):
                    ln_check = cmd_type.match(line)
                    if ln_check.group() == "python gus_cases_vault.py":
                        #os.environ['https_proxy'] = "http://public-proxy1-0-sfm.data.sfdc.net:8080/"
                        logging.debug(line)
                        retcode = os.system(line)
                        logging.debug(retcode)
                        if retcode != 0:
                            pods_match = pods.findall(line)
                            logging.debug(pods_match)
                            failed_plans.append(pods_match)
                    else:
                        #os.environ['https_proxy'] = ""
                        logging.debug(line)
                        retcode = os.system(line)
                        logging.debug(retcode)
                        if retcode != 0:
                          logging.debug(line)
    else:
        logging.debug("cases.sh file not found!")
        logging.debug(case_file)
        sys.exit(1)
    return failed_plans

def list_roles(sets):
    role_list = []
    for key in sets.iterkeys():
        role_list.append(str(key))
    role_list.sort()
    print "Roles:"
    for item in role_list:
        print item
    print "\nTotal Roles: %s" % (len(role_list))
    sys.exit(0)

def find_role(sets):
    results = []
    role_search = re.compile(r'%s' % options.search_role)
    for key in sets.iterkeys():
        if role_search.findall(key):
            results.append(str(key))
    if not results:
        print "No Roles found matching that name."
        sys.exit(1)
    else:
        for result in results:
            print result
        return results
    #sys.exit(0)


def dryrun():
    if not options.dryrun:
        failures = case_executor()
        if failures:
            for fail in failures:
                logging.debug(str(fail) + " failed to generate implementation plans.")
            sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Case Builder Program    ')
    parser.add_argument("--dry-run", action="store_true", dest="dryrun",
                        help="Dry run of build no case will be generated.")
    parser.add_argument("-l", "--list", action="store_true", dest="list", help="List active role classes.")
    parser.add_argument("--full", action="store_true", dest="full_list", help="View presets of a roleclass.")
    parser.add_argument("-s", dest="search_role", help="Search for a role.")
    parser.add_argument("--roleclass", dest="roleclass", help="Role Class")
    parser.add_argument("--podgroup", dest="podgroup", help="Hostlist file for role.")
    parser.add_argument("--groupsize", dest="groupsize", help="Groupsize.")
    parser.add_argument("--taggroups", dest="taggroups", help="Taggroups.")
    parser.add_argument("--bundle", dest="bundle", default="None", help="Patch Bundle.")
    parser.add_argument("--subject", dest="subject", help="Subject.")
    parser.add_argument("--dowork", dest="dowork", help="Task to perform")
    parser.add_argument("--clusstat", dest="cluststat", help="Cluster Status.")
    parser.add_argument("--hoststat", dest="hoststat", help="Host Status.")
    parser.add_argument("-r", dest="regex", help="Regex Filter")
    parser.add_argument("-f", dest="filter", help="Filter")
    parser.add_argument("--host_validation", dest="host_validation", action="store_true", default=False, help="Flag to verify remote hosts")
    parser.add_argument("--auto_close_case", dest="auto_close_case", action="store_true", default=True, help="To close the cases during "
                                                                                                         "execution")
    # Added as per W-3779869 to skip linebacker
    parser.add_argument("--nolinebacker", dest="nolinebacker", action="store_true", default=False, help="Don't use line backer")

    parser.add_argument("--canary", dest="canary", action ="store_true", help="All canary cases")
    options = parser.parse_args()

    initfile()  # function to clean existing cases.sh file
    logging.basicConfig(level=logging.DEBUG)
    sets = json_imports()
    if options.full_list and options.roleclass:
        pp = pprint.PrettyPrinter(indent=2)
        pp.pprint("Presets contents for %s" % (options.roleclass))
        pp.pprint("=====================================================")
        try:
            pp.pprint(sets[options.roleclass])
            sys.exit(0)
        except KeyError:
            logging.error("No such role %s in presets.", options.roleclass)
            sys.exit(1)
    elif options.full_list and not options.roleclass:
        logging.error("Usage: No role specified to search.")
    if options.search_role:
        find_role(sets)
    if options.list:
        list_roles(sets)
    if options.roleclass:
        cmd_builder(sets)
        dryrun()
    elif options.canary:
        options.search_role = 'canary'
        canary_cases = find_role(sets)
        for canary in canary_cases:
            cmd_builder(sets, canary)
        dryrun()
