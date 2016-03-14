#!/usr/bin/python
#
#
import json
import subprocess
from subprocess import PIPE,Popen
import os
import cmd

def json_imports():
    presets = "case_presets.json"
    ver = "valid_versions.json"
    with open(presets, 'r') as p:
        sets = json.load(p)

    #with open(ver, 'r') as v:
        #bundles = json.load(v)
    return sets

def pod_builder(sets):
    role = os.environ['ROLE'].lower()
    bundle = os.environ['BUNDLE']
    dr = os.environ['DR']
    canary = os.environ['CANARY']
    monthDict={'01':'Jan', '02':'Feb', '03':'Mar', '04':'Apr', '05':'May', '06':'Jun', '07':'Jul', '08':'Aug', '09':'Sep', '10':'Oct', '11':'Nov', '12':'Dec'}
    mon = monthDict[bundle.split('.')[1]]

    if os.environ['DR'] == "false":
        status = "Prod"
    else:
        status = "DR"

    if os.environ['CANARY'] == "false":
        group_file = sets[role][status]['PODGROUP']
        template = sets[role][status]['TEMPLATEID']
        gsize = sets[role][status]['GROUPSIZE']
        tagsize = sets[role][status]['TAGGROUPS']

        cmd = "python bin/pods_cases.py -p hostlists/%s -r %s -t %s -b %s -d %s -s %d -g \"%s\" --patchset %s --taggroups %d" % (group_file, role, template, mon.lower(), dr.title(), gsize, status, bundle, tagsize)
        p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
        with open("cases.sh", 'w') as f:
            f.write(p.stdout.read())
    else:
        group_file = sets[role]['CANARY'][status]['PODGROUP']
        template = sets[role]['CANARY'][status]['TEMPLATEID']
        gsize = sets[role]['CANARY'][status]['GROUPSIZE']
        tagsize = sets[role]['CANARY'][status]['TAGGROUPS']
        
        cmd = "python bin/pods_cases.py -p hostlists/%s -r %s -t %s -b %s -d %s -s %d -g \"%s\" --patchset %s --taggroups %d" % (group_file, role, template, mon.lower(), dr.title(), gsize, status, bundle, tagsize)
        p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
        with open("cases.sh", 'w') as f:
            f.write(p.stdout.read())

if __name__ == "__main__":
    sets = json_imports()
    pod_builder(sets)
        
    
    
    

    
    
