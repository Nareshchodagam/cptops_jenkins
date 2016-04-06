#Jenkins scripts.

_Adding to case_presets.json_

_JSON Format_

		"role_title":{
			"PROD|DR":{
						"PODGROUP": Hostlists file for pod_cases.py
						"TEMPLATEID":Template to use,
						"GROUPSIZE": Default group size,
						"TAGGROUPS":Default taggroups,
						"FILTER": Optional Filters
						"INFRA":Primary, Secondary or Supporting Infrastructure
						"ROLE": Application role. 
					}
			}
	
_Example_

			"search(21|22,41|42)_prod":{
				"PROD":{
					"PODGROUP":"pod.pri",
					"TEMPLATEID":"search",
					"GROUPSIZE":15,
					"TAGGROUPS":0,
					"FILTER":["search(21|22)-", "search(41|42)-"],
					"INFRA":"Primary",
					"ROLE":"search"
					}
			},

_case_builder Jenkins job_

After updating the case_presets file the following steps need to be done for 
the case_builder jenkins job.  

	1. Update the ROLE_CLASS parameter with the new role_title. In the job the list is sorted. 
	2. If you job contains any filters update the groovy script with the associated filters for the ROLE_CLASS. 
			Example. 
					if (ROLE_CLASS.equals("FFX_CANARY_PROD")) {
						return ["(1|2)-[2-6]"]
					}
	3. If you job has a special Subject tile then update the groovy script with the title for that ROLE_CLASS.
			Example. 
					 if (ROLE_CLASS.equals("SEARCH(21|22,41|42)_DR") || ROLE_CLASS.equals("SEARCH(21|22,41|42)_PROD")){
					     return ["\"DR 20's\"", "\"DR 40's\"", "\"PROD 20's\"", "\"PROD40's\""]
	4. Run the docker-case-builder job under Docker Builds to rebuild the case_builder image. 
	
