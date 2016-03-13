#!/usr/bin/python
#
#
import json
import subprocess
from subprocess import PIPE,Popen
import sets
import os
import cmd

def json_imports():
    presets = "case_presets.json"
    ver = "valid_versions.json"
    with open(presets, 'r') as p:
        sets = json.load(p)
    
    with open(ver, 'r') as v:
        bundles = json.load(v)
    
    return sets,bundles    
    
def pod_builder(sets, bundles):
    role = os.environ['ROLE']
    bundle = os.environ['BUNDLE']
    dr = os.environ['DR']
    canary = os.environ['CANARY']
    monthDict={'01':'Jan', '02':'Feb', '03':'Mar', '04':'Apr', '05':'May', '06':'Jun', '07':'Jul', '08':'Aug', '09':'Sep', '10':'Oct', '11':'Nov', '12':'Dec'}
    mon = monthDict[bundle.split('.')[1]]
    if dr:
        status = "Prod"
    else:
        status = "DR"
    
    if not canary:
        group_file = sets[role][status]['PODGROUP']
        template = sets[role][status]['TEMPLATEID']
        gsize = sets[role][status]['GROUPSIZE']
        tagsize = sets[role][status]['TAGGROUPS']
        
        cmd = "python pods_cases.py -p %s -r %s -t %s -b %s -d %s -s %d -g \"%s\" --patchset %s --taggroups %d" (group_file, role, template, mon, dr, gsize, status, bundle, tagsize)
        print cmd
        
if __name__ == "__main__":
    (sets, bundles) = json_imports()
    pod_builder(sets, bundles)
        
    
    
    

    
    
