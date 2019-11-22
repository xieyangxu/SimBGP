import yaml
import os.path
import copy

from BGPutils import *

trace = 'bistable'

# load control plane and invariants from yaml file
ws_path = os.path.abspath(os.path.dirname(__file__))

cp_path = os.path.join(ws_path, 'traces/'+trace+'_network.yml')
with open(cp_path) as f:
    cp = yaml.load(f, Loader=yaml.SafeLoader)
# cp should be read-only, dp state are maintained seperately
dp = copy.deepcopy(cp)
for device in dp['Devices']:
    device.pop('BgpConfig', None)
    device['ForwardingTable'] = copy.deepcopy(device['StaticRoutes'])
    device.pop('StaticRoutes', None)

iv_path = os.path.join(ws_path, 'traces/'+trace+'_invariants.yml')
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
    for policy in device['BgpConfig'][1]['InboundPolicies']:
        policy_dict[policy['Name']] = policy
    for policy in device['BgpConfig'][2]['OutboundPolicies']:
        policy_dict[policy['Name']] = policy

# BGP state data structure: rib
"""rib stucture demo:
    r1:
      1.1.1.1/32:
        Prefix: 1.1.1.1/32:
        ASPath: [r2, r3]
        Tag: {1, 7}
        Interface: r1@Eth1
        LocalPref: 100
      # locally originated routes
      10.0.0.1/32:
        Prefix: 10.0.0.1/32:
        ASPath: []
        Tag: {}
        Interface: null
        LocalPref: 100
    r2:
      1.1.1.1/32:
        Prefix: 1.1.1.1/32:
        ASPath: [r3]
        Tag: {1}
        Interface: r2@Eth2
        LocalPref: 100
"""
rib = {
    device['Name']: {}
    for device in cp['Devices']
}

# init RIB with advertised routes
for device in cp['Devices']:
    for prefix in device['BgpConfig'][0]['AdvertisedRoutes']:
        rib[device['Name']][prefix] = rib_entry_init(prefix)

bgp_init(rib, cp, device_dict, interface_dict, policy_dict)

iterate_rib(order=['r1','r2','r3'])
print(rib)
