#!/usr/bin/python
#
#
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
            'regexfilter': '--regexfilter',
            'casetype': '--casetype',
            'dowork': '--dowork',
            'clusteropstat': '--clusteropstat',
            'hostopstat': '--hostopstat',
            'subject': '-g',
            'idb': '--idb',
            'impl_plan': '--implplan'}

req_sub = ['search(23|43)_prod',
           'search(21|22,41|42)_prod',
           'search(21|22,41|42)_prod',
           'search(23|43)_dr',
           'search(21|22,41|42)_dr']
