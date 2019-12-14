import yaml
import os.path
import copy
import argparse
from itertools import combinations
from tryAP.main import dp_check

from BGPutils import *
from FTutils import *

# parser = argparse.ArgumentParser(description='Process some integers.')
# parser.add_argument('-d', '--dir', metavar='d', nargs=1, default=[str(os.path.abspath(
#     os.path.dirname(__file__)))], help='directory to look for traces folder')
# parser.add_argument('trace', metavar='t', type=str, nargs=1,
#                     help='trace name. try `sample` or `bistable`')

# args = parser.parse_args()
# trace = args.trace[0]
trace = 'netv'

ws_path = os.path.abspath(os.path.dirname(__file__))

cp_path = os.path.join(ws_path, 'traces/network/'+trace+'_network.yml')

# load control plane and invariants from yaml file
#ws_path = os.path.abspath(args.dir[0])

def cp_init(cp):
    for device in cp['Devices']:
        for interface in device['Interfaces']:
            interface['FailFlag'] = False

def cp_load(cp_path):
    with open(cp_path) as f:
        cp = yaml.load(f, Loader=yaml.SafeLoader)
    cp_init(cp)
    return cp

def dp_init(cp):
    # cp should be read-only, dp state are maintained seperately
    dp = copy.deepcopy(cp)
    for device in dp['Devices']:
        device.pop('BgpConfig', None)
        device['ForwardingTable'] = copy.deepcopy(device['StaticRoutes'])
        device.pop('StaticRoutes', None)
    return dp

def rib_init(cp):
    # BGP state data structure: rib
    """rib stucture demo:
        r1:
        1.1.1.1/32:
            - Prefix: 1.1.1.1/32:
            ASPath: [r2, r4]
            Tag: {1, 7}
            Interface: r1@Eth1
            LocalPref: 100
        # locally originated routes
        10.0.0.1/32:
            - Prefix: 10.0.0.1/32:
            ASPath: []
            Tag: {}
            Interface: null
            LocalPref: 100
        r2:
        1.1.1.1/32:
            # multipath enabled
            - Prefix: 1.1.1.1/32:
            ASPath: [r4]
            Tag: {1}
            Interface: r2@Eth2
            LocalPref: 200
            - Prefix: 1.1.1.1/32:
            ASPath: [r3, r4]
            Tag: {}
            Interface: r2@Eth3
            LocalPref: 200
    """
    rib = {
        device['Name']: {}
        for device in cp['Devices']
    }

    # init RIB with advertised routes
    for device in cp['Devices']:
        for prefix in device['BgpConfig']['AdvertisedRoutes']:
            rib[device['Name']][prefix] = [rib_entry_init(prefix)]
    return rib

def cp_check(cp, query, device_dict, interface_dict, policy_dict):
    rib = rib_init(cp)

    bgp_init(rib, cp, device_dict, interface_dict, policy_dict)

    bgp_iterate([device['Name'] for device in cp['Devices']])
    # print(rib)

    dp = dp_init(cp)
    ft_build_from_rib(rib, dp, device_dict)

    return dp_check(dp, query)

def cp_failure_reasoning(query):

    cp = cp_load(cp_path)
    
    # build name dict for devices and interfaces
    device_dict = {
        device['Name']: device
        for device in cp['Devices']
    }
    interface_dict = {
        interface['Name']: interface
        for device in cp['Devices'] for interface in device['Interfaces']
    }
    policy_dict = {}
    for device in cp['Devices']:
        for policy in device['BgpConfig']['InboundPolicies']:
            policy_dict[policy['Name']] = policy
        for policy in device['BgpConfig']['OutboundPolicies']:
            policy_dict[policy['Name']] = policy
    
    # build links list
    links = []
    linked_set = set()
    for interface_name, interface in interface_dict.items():
        if interface['Neighbor'] != None:
            if interface['Neighbor'] not in linked_set:
                links.append([interface_name, interface['Neighbor']])
                linked_set.add(interface_name)


    max_failure = query['MaxFailures']

    """failures demo structure: list of set of list
        - ['r1@Eth1', 'r2@Eth1']
          ['r1@Eth2', 'r3@Eth1']
        - ['r1@Eth1', 'r2@Eth1']
          ['r2@Eth2', 'r4@Eth1']
    """
    failures = []
    # build all failure cases under a maximum ammount
    for i in range(max_failure + 1):
        failures = list(combinations(links, i)) + failures

    res = True
    for failure_case in failures:
        cp_init(cp) # clear all flags
        for failed_link in failure_case:
            for end_node in failed_link:
                interface_dict[end_node]['FailFlag'] = True

        res &= cp_check(cp, query, device_dict, interface_dict, policy_dict)
        if res == False:
            break

    print(res)


    

if __name__ == "__main__":
    

    iv_path = os.path.join(ws_path, 'traces/invariants/'+trace+'_invariants.yml')
    with open(iv_path) as f:
        iv = yaml.load(f, Loader=yaml.SafeLoader)

    qu = iv['Reachability']
    for query in qu:
        cp_failure_reasoning(query)

