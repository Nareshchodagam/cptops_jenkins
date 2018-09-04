#!/usr/bin/python
#
#
opt_dict = {'gsize': '-s',
            'role': '-r',
            'podgroup': '-p',
            'template': '-t',
            'status': '-d',
            'patchset': '--patchset',
            'tagsize': '--taggroups',
            'infra': '--infra',
            'filter': '-f',
            'regexfilter': '--regexfilter',
            'casetype': '--casetype',
            'dowork': '--dowork',
            'clusteropstat': '--clusteropstat',
            'hostopstat': '--hostopstat',
            'subject': '-g',
            'idb': '--idb',
            'excludes': '--exclude',
            'list_filter': '--HLGrp',
            'impl_plan': '--implplan',
            'no_host_validation': '--no_host_validation',
            'auto_close_case': '--auto_close_case',
            'nolinebacker': '--nolinebacker',
            'hostpercent': '--hostpercent',
            'casesubject': '--casesubject',
            'delpatched': '--delpatched',
	        'skip_bundle': '--skip_bundle',
            'bpv2': '--bpv2',
            'csv': '--csv'}

req_sub = ['search(23|43)_prod',
           'search(21|22,41|42)_prod',
           'search(21|22,41|42)_prod',
           'search(23|43)_dr',
           'search(21|22,41|42)_dr',
           'appauth_prod',
           'appauth_canary_prod',
           'vc_prod',
           'vc_canary_prod',
           'cmgt_passive_prod',
           'monitor_standby_prod',
           'monitor_primary_prod',
           'monitor_canary_prod',
           'argus_writed_matrics_prod',
           'argus_writed_matrics_canary_prod',
           'netmgt_prod',
           'siteproxy_prod',
           'coreafw_canary_prod',
           'coreafw_cbatch_dapp_canary_prod']
