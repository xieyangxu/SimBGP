import yaml
import os.path
import copy
import argparse
from tryAP.main import main

from BGPutils import *
from FTutils import *

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('-d', '--dir', metavar='d', nargs=1, default=[str(os.path.abspath(
    os.path.dirname(__file__)))], help='directory to look for traces folder')
parser.add_argument('trace', metavar='t', type=str, nargs=1,
                    help='trace name. try `sample` or `bistable`')

args = parser.parse_args()
trace = args.trace[0]

# load control plane and invariants from yaml file
ws_path = os.path.abspath(args.dir[0])

cp_path = os.path.join(ws_path, 'traces/network/'+trace+'_network.yml')
with open(cp_path) as f:
    cp = yaml.load(f, Loader=yaml.SafeLoader)
# cp should be read-only, dp state are maintained seperately
dp = copy.deepcopy(cp)
for device in dp['Devices']:
    device.pop('BgpConfig', None)
    device['ForwardingTable'] = copy.deepcopy(device['StaticRoutes'])
    device.pop('StaticRoutes', None)

iv_path = os.path.join(ws_path, 'traces/invariants/'+trace+'_invariants.yml')
with open(iv_path) as f:
    iv = yaml.load(f, Loader=yaml.SafeLoader)

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

bgp_init(rib, cp, device_dict, interface_dict, policy_dict)

bgp_iterate([device['Name'] for device in cp['Devices']])
# print(rib)

ft_build_from_rib(rib, dp, device_dict)

# output dataplane file in ./traces/dataplane/
dp_dir = os.path.join(ws_path, 'traces/dataplane/')
if not os.path.exists(dp_dir):
    os.makedirs(dp_dir)

dp_path = os.path.join(ws_path, 'traces/dataplane/'+trace+'_dataplane.yml')
with open(dp_path, 'w') as f:
    yaml.dump(dp, f)

# output reachability query file in ./traces/query/
# run dataplane verification
if 'Reachability' in iv:
    qu = iv['Reachability']

    qu_dir = os.path.join(ws_path, 'traces/query/')
    if not os.path.exists(qu_dir):
        os.makedirs(qu_dir)

    qu_path = os.path.join(ws_path, 'traces/query/'+trace+'_query.yml')
    with open(qu_path, 'w') as f:
        yaml.dump(qu, f)

    # call tryAP with dataplane query
    main(trace, ws_path)


# def check_case(case):
#     for check in case['Case']:
#         routing_rules = rib[check['Device']]
#         prefix_rules = routing_rules[check['Prefix']]
#         interfaces = check['Interfaces']
#         if not all((rule['Interface'] in interfaces) for rule in prefix_rules):
#             return False
#     return True


# def check_routing_rule(rr):
#     return any(check_case(case) for case in rr)


# rr = iv['RoutingRules']
# print("Routing Rules:")
# for case in rr:
#     print(check_case(case))
