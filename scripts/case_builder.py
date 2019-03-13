#!/usr/bin/python
#
#
'''
    Jenkins Python script to create implementation plans and create cases.
'''
import argparse
import json
import logging
import os
import pprint
import re
import subprocess
import sys
from functools import partial
from operator import attrgetter

import case_opts as co


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
    bld_cmd['template'] = options.template if options.template != None else sets[role_class][role_status]['TEMPLATEID']

    try:
        bld_cmd['patching'] = sets[role_class][role_status]['PATCHING']
    except KeyError:
        bld_cmd['patching'] = "majorset"

    if 'IMPLPLAN' in sets[role_class][role_status].keys():
        bld_cmd['impl_plan'] = "templates/"+sets[role_class][role_status]['IMPLPLAN']+".json"

    if options.hostpercent:
        bld_cmd['hostpercent'] = options.hostpercent
    if options.os:
        bld_cmd['os'] = options.os
    if options.delpatched:
        bld_cmd['delpatched'] = options.delpatched
    if options.cluststat:
       bld_cmd['clusteropstat'] = options.cluststat
    if options.hoststat:
        bld_cmd['hostopstat'] = options.hoststat
    if options.auto_close_case:
        bld_cmd['auto_close_case'] = options.auto_close_case
    if options.nolinebacker:
        bld_cmd['nolinebacker'] = options.nolinebacker
    if options.casesubject:
        bld_cmd['casesubject'] = options.casesubject


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
    if options.skip_bundle:
	bld_cmd['skip_bundle'] = options.skip_bundle
    # This change will help user to choose the way he/she wants to create case.

    if 'prsn' in bld_cmd['role'] or 'chan' in bld_cmd['role']: # To make sure we are not using host_validation during UMPS case creation
        bld_cmd['no_host_validation'] = '--no_host_validation'

    if options.no_host_v:
        bld_cmd['no_host_validation'] = options.no_host_v
    if options.csv:
        bld_cmd['csv'] = options.csv
    if 'CL_STATUS' in sets[role_class][role_status].keys():
        bld_cmd['clusteropstat'] = sets[role_class][role_status]['CL_STATUS']
    if 'HO_STATUS' in sets[role_class][role_status].keys():
        bld_cmd['hostopstat'] = sets[role_class][role_status]['HO_STATUS']
    if 'HOSTPERCENT' in sets[role_class][role_status].keys():
        bld_cmd['hostpercent'] = sets[role_class][role_status]['HOSTPERCENT']

    #Custom parameters within the case_presets.json
    #These options are not within each predefined role_class.
    #So we test if values are present.
    for key in ['CASETYPE', 'IMPL_PLAN', 'EXCLUDES','LIST_FILTER']:
        if key in sets[role_class][role_status]:
            if key == 'EXCLUDES':
                bld_cmd[str.lower(key)] = "hostlists/" + sets[role_class][role_status][key]
            else:
                bld_cmd[str.lower(key)] = sets[role_class][role_status][key]

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

    if 'CL_STATUS' in sets[role_class][role_status].keys() or options.cluststat:
        logging.debug("CL_STATUS = " + bld_cmd['clusteropstat'])

    if 'HO_STATUS' in sets[role_class][role_status].keys() or options.hoststat:
        logging.debug("HO_STATUS = " + bld_cmd['hostopstat'])

    if 'HOSTPERCENT' in sets[role_class][role_status].keys() or options.hostpercent:
        logging.debug("HOSTPERCENT = " + bld_cmd['hostpercent'])

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
            if opt == 'no_host_validation' and bld_cmd['no_host_validation'] != '':
                pod_cmd.append(co.opt_dict[opt])
                continue
            pod_cmd.append(co.opt_dict[opt])
            pod_cmd.append(str(bld_cmd[opt]))
    if options.filtergia == True:
        pod_cmd.append(str("--filter_gia"))
    if options.bpv2 == True:
        pod_cmd.append(str("--bpv2"))
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

def readFile(jsonFile):
    """
    Reads and json file and return a dict object.
    :param JsonFile: json file
    :return: dict object
    """
    with open(jsonFile, 'r') as fd:
        res = json.load(fd)
    return res

def bundleName(fn, file, bundle):
    """
    :param fn: read a json file
    :param file: json file
    :param bundle: bundle name
    :return: bundle name from povided json file and bundle name provided by user.
    """
    bundle = attrgetter('lower')(bundle)()
    bundleData = fn(file)
    osVers = bundleData.get('CENTOS').keys()
    #sub = max(bundleData.get('CENTOS').get('6').keys())
    osSix = bundleData.get('CENTOS').get('6')
    osSixCurrent = osSix['current']['sfdc-release']
    osSeven = bundleData.get('CENTOS').get('7')
    osSevenCurrent = osSeven['current']['sfdc-release']
    if osSixCurrent != osSevenCurrent:
        sub = osSixCurrent+"/"+osSevenCurrent
    else:
        sub = osSixCurrent
    return sub, bundle

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Case Builder Program    ')
    parser.add_argument("--dry-run", action="store_true", dest="dryrun",
                        help="Dry run of build no case will be generated.")
    parser.add_argument("-l", "--list", action="store_true", dest="list", help="List active role classes.")
    parser.add_argument("--full", action="store_true", dest="full_list", help="View presets of a roleclass.")
    parser.add_argument("-s", dest="search_role", help="Search for a role.")
    parser.add_argument("--roleclass", dest="roleclass", help="Role Class")
    parser.add_argument("--template", dest="template", help="Template to use")
    parser.add_argument("--podgroup", dest="podgroup", help="Hostlist file for role.")
    parser.add_argument("--groupsize", dest="groupsize", help="Groupsize.")
    parser.add_argument("--taggroups", dest="taggroups", help="Taggroups.")
    parser.add_argument("--bundle", dest="bundle", default=None, help="Patch Bundle.")
    parser.add_argument("--skip_bundle", dest="skip_bundle", help="Skip Bundle.")
    parser.add_argument("--subject", dest="subject", help="Subject.")
    parser.add_argument("--dowork", dest="dowork", help="Task to perform")
    parser.add_argument("--hostpercent", dest="hostpercent", help="Host percentage")
    parser.add_argument("--clusstat", dest="cluststat", help="Cluster Status.")
    parser.add_argument("--hoststat", dest="hoststat", help="Host Status.")
    parser.add_argument("--filter_gia", dest="filtergia", action="store_true", default="False", help="Filter GIA host")
    parser.add_argument("-r", dest="regex", help="Regex Filter")
    parser.add_argument("-f", dest="filter", help="Filter")
    parser.add_argument("--no_host_validation", dest="no_host_v", action="store_true", help="Flag to skip verify remote hosts")
    parser.add_argument("--auto_close_case", dest="auto_close_case", action="store_true", default=True, help="To close the cases during "
                                                                                                         "execution")
    parser.add_argument("-x", "--bpv2", dest="bpv2", action="store_true", default="False", help="Create cases with Build-Plan_v2")
    # Added as per W-3779869 to skip linebacker
    parser.add_argument("--nolinebacker", dest="nolinebacker", action="store_true", default=False, help="Don't use line backer")
    # W-4531197 Adding logic to remove already patched host for Case.
    parser.add_argument("--delpatched", dest="delpatched", action='store_true', help="command to remove patched host.")
    parser.add_argument("--casesubject", dest="casesubject", help="Initial case subject to use")

    #Added to filter C6 and C7 hosts while cases creation using build_Plan v1
    parser.add_argument("--os", dest="os", help="command to filter hosts based on major set, Valid Options are 6 and 7")

    #End

    parser.add_argument("--canary", dest="canary", action ="store_true", help="All canary cases")
    parser.add_argument("--csv", dest="csv", help="Read given CSV file and create cases as per the status, --hoststat is optional comma separated status Default is DECOM, --role is optional default take all roles")
    parser.add_argument("--role", dest="role",help="provide a single or comma seperated role names, this option is optional with --csv. Default is ALL")
    options = parser.parse_args()

    initfile()  # function to clean existing cases.sh file
    logging.basicConfig(level=logging.DEBUG)
    sets = json_imports()

    if options.os:
        if options.os != "6" and options.os != "7":
            print("\n--os valid options are 6 and 7, provided {0}\n".format(options.os))
            sys.exit(1)

    if options.delpatched and not options.bundle:
        print("\n\n'--delpatched' should be called with '--bundle' option only, instead use '--skip_bundle' option.\n\n")
        exit(1)

    if not options.bundle:
        verFile = os.path.join(os.environ["HOME"], "git/cptops_validation_tools/includes/valid_versions.json")
        bundleOut = partial(bundleName, file=verFile, bundle='current')
        options.casesubject, options.bundle = bundleOut(readFile)

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

    #W-4546859 - Create cases of hosts provide in CSV file basically a sheet given by security.
    if options.csv:
        from secdata import Secsheet
        sec = Secsheet()
        if not options.hoststat:
            print("Host state not provided, default is DECOM.")
            options.hoststat = 'DECOM'
        options.hoststat = options.hoststat.lower()
        role = options.role
        if options.hoststat != 'active':
            for state in options.hoststat.upper().split(','):
                if not re.search(r'DECOM|HW_PROVISIONING|PRE_PRODUCTION|PROVISIONING', state):
                    print("\nProvided iDB state not Found. state {0} is not the correct coice.\n".format(state))
                    exit(1)
            sets, data = sec.gen_plan(options.bundle, options.csv, options.hoststat, role)
        elif options.hoststat == 'active':
            print("\nUse Command to generate cases for active left over hosts")
            print("python case_builder.py --roleclass <role> --bundle <bundle.name> --dowork all_updates --delpatched\n")
            exit(0)
        else:
            print("--hoststat must be one or multiple comma seperated of , 'decom|active|hw_provisioning|pre_production|provisioning'")
            sys.exit(1)
        for rcl in sets.keys():
            if re.search(r'app|cbatch|dapp', rcl):
                options.hostpercent = "33"
            options.roleclass = rcl
            cmd_builder(sets)
            dryrun()

        print( "\nGenerating Cases for role %s with status %s." % ('ALL' if not role else role.upper(), options.hoststat))
        print("\nScanned roles from CSV... {0}\n".format(data.keys()))
    #END

    elif options.canary:
        options.search_role = 'canary'
        canary_cases = find_role(sets)
        for canary in canary_cases:
            cmd_builder(sets, canary)
        dryrun()

