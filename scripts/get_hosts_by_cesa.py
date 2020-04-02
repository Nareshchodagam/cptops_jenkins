#!/usr/bin/env python

import logging
import re

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# stop seeing cert related warning while querying atlas
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = logging.getLogger(__name__)


def split_list(s_list):
    """
    A function to split the input list argument by half.
    Since Atlas doesn't support more than 5 query string parameters, this will break down the query string in half
    if they are more then 5.
    :param s_list: list
    :return: tuple
    """
    logger.info("Split the list %s by half", s_list)
    half = len(s_list) // 2
    logger.debug("CESA's going to process %s", half)
    return s_list[:half], s_list[half:]


def group_pods(podlist, cluster_type=None):
    """
    This Function takes the podlist as input and return a new podlist based on DR/PROD.
    It also filterout the podlist based on clusterType if given in the case_presets.json file.
    :param list podlist: A list of pods. [[{u'clusterDr': True,
                                        u'clusterName': u'NA53',
                                        u'clusterStatus': u'DECOM',
                                        u'clusterType': u'POD',
                                        u'datacenterName': u'phx',
                                        u'hostName': u'na53-proxy2-1-phx',
                                        u'hostOs': u'7',
                                        u'superpodName': u'SP4'}]]
    :param string cluster_type: A clusterType to filter PODS
    :return:
    """
    pods = {"prod": [], "dr": []}
    for pod in podlist:
        # 'pod' is a list which has only one item, we leave the list behind and take only the dict within
        try:
            this_pod = pod[0]
            if cluster_type:
                if re.search(r"|".join(cluster_type.split(",")), this_pod["clusterType"], re.IGNORECASE):
                    podlist_format = [
                        this_pod["clusterName"], this_pod["datacenterName"].upper(), this_pod["superpodName"],
                        this_pod["clusterStatus"]
                    ]
            else:
                podlist_format = [
                    this_pod["clusterName"], this_pod["datacenterName"].upper(), this_pod["superpodName"],
                    this_pod["clusterStatus"]
                ]

            # Skip non-ACTIVE clusters
            if this_pod["clusterStatus"] != "ACTIVE":
                continue

            # Segregate the PODS based on DR/PROD
            if this_pod["clusterDr"]:
                pods["dr"].append(podlist_format)
            else:
                pods["prod"].append(podlist_format)
        except BaseException as error:
            logger.exception(error)
    logger.debug("Grouped podlist ")
    return pods


def write_files(data, podlist_file):
    """
    This Function will take a list as input and write a PODlist to podlit file added in case_presets.json for a role
    :param list data: Podlist data to write
    :param string podlist_file: Podlist file name
    """
    exclude_dcs = ["chx", "wax", "ttd", "hio"]
    try:
        file_loc = "/root/git/cptops_case_gen/hostlists/{0}".format(podlist_file)
        logger.info("Opening podlist %s for writing", file_loc)
        with open(file_loc, "w") as f:
            for item in data:
                podlist_line = " ".join(item)
                if not any(dc in podlist_line for dc in exclude_dcs):
                    f.write(podlist_line + "\n")
        logger.info("Podlist file %s written successfully", file_loc)
    except IOError as error:
        logger.exception(error)


def remove_dups(filename):
    """
    This Function is used to remove the Duplicate lines from podlist file.
    :param string filename: Podlist filename to open
    """
    filename = "/root/git/cptops_case_gen/hostlists/" + filename
    uniqlines = set(open(filename).readlines())
    with open(filename, "w") as f:
        f.writelines(set(uniqlines))
    logger.info("Duplicates removed from podlist file %s", filename)


class Atlas:
    """
    This class is use to extract hosts information from Atlas
    """
    def __init__(self):
        self.atlas_url = "https://ops0-cpt1-1-xrd.eng.sfdc.net:9876/api/v1"
        self.cesa_end_point = "/vulnerability-details/"
        self.cesa_query_filter = "hosts?cesa="
        self.host_query_filter = "/hosts?name="
        self.host_fields = ",clusterStatus=ACTIVE,hostStatus=ACTIVE&fields=clusterName,datacenterName," \
                           "superpodName,clusterStatus,clusterDr,clusterType,hostName,hostOs"
        self.current_bundle = "/patch-bundles?current=true"

    def atlas_query(self, cesa=None, host=None, current=None):
        """
        This function is used to query Atlas for getting
        1. Hosts impacted by  given CESA
        2. Query host  attributes like clusterDr, clustertype hostOs etc..

        :param string cesa: A CESA string to query Atlas e.g "CESA-2019:4326,CESA-2019:4256,CESA-2020:0374"
        :param string host: A hostname to query Atlas
        :return json: return a json dictionary
        """
        url = None
        if cesa:
            url = "{0}{1}{2}{3}".format(self.atlas_url, self.cesa_end_point, self.cesa_query_filter, cesa)
            logger.info("Fetching hosts details for CESA [%s] from URL %s ", cesa, url)
        elif host:
            url = "{0}{1}{2}{3}".format(self.atlas_url, self.host_query_filter, host, self.host_fields)
            logger.info("Fetching data from atlas for host [%s] URL %s ", host, url)
        elif current:
            url = "{0}{1}".format(self.atlas_url, self.current_bundle)
            logger.info("Fetching data from URL %s", url)

        session = requests.Session()
        try:
            result = session.get(url, verify=False)
            logger.debug("Returned Status code from Atlas %s for url %s ", result.status_code, url)
            return result.json()
        except requests.exceptions.RequestException as e:
            logger.exception("Exception %s from Atlas url %s ", e, url)
            raise SystemExit(e)

    def get_cesas_hosts(self, cesas):
        """
        This method queries Atlas to extract hosts impacted by CESA (single or multiple ) and finally combined
        all the returned data into a single data structure.

        :param string cesas: A list of cesa's
        :return dict: A dictionary of key as rolename and value a list containing all the CESA impacted hosts
        """

        if len(cesas.split(",")) <= 5:  # If total CESA to query is less than 5
            all_cesa = self.atlas_query(cesas)
            logger.info("Extracted all the hosts from CESA ( less then or equal to 5 ) [%s] ", cesas)
            logger.debug("All impacted hosts %s  ", all_cesa)
        else:  # If total CESA to query is more than 5, break it down
            cesas_list1, cesas_list2 = split_list(cesas.split(","))
            all_cesa = dict()
            out = self.atlas_query(",".join(cesas_list1))
            out1 = self.atlas_query(",".join(cesas_list2))
            logger.info("Extracted all the hosts from CESA ( less then or equal to 5 ) %s - ", cesas)
            logger.debug("All impacted hosts %s - ", all_cesa)

            # Combined the two returned data structure into a single one.
            dict_keys = set(out.keys() + out1.keys())  # Get unique keys from both dict keys
            for i in dict_keys:
                if (i in out) and (i in out1):
                    all_cesa[i] = list(set(out[i] + out1[i]))
                elif (i in out) and (i not in out1):
                    all_cesa[i] = out[i]
                elif (i in out1) and (i not in out):
                    all_cesa[i] = out1[i]
            logger.info("Successfully extracted hosts for all given CESA [%s]  ", cesas)
        return all_cesa

    def get_pods(self, host):
        """
        This method is used to fetch hosts attribiutes from Atlas.
        :param string host: A hostname
        :return json: A dict containing hosts attributes.
        """
        host_details = self.atlas_query(host=host)
        logger.debug("Host %s attributes %s - ", host, host_details)
        return host_details
