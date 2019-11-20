import yaml
import os.path
import copy

from BGPutils import *

trace = 'sample'

# load control plane and invariants from yaml file
ws_path = os.path.abspath(os.path.dirname(__file__))

cp_path = os.path.join(ws_path, 'traces/'+trace+'_network.yml')
with open(cp_path) as f:
    cp = yaml.load(f, Loader=yaml.SafeLoader)
dp = copy.deepcopy(cp) # cp should be read-only, dp state are maintained seperately
for device in dp['Devices']:
    device.pop('BgpConfig', None)
    device['ForwardingTable'] = copy.deepcopy(device['StaticRoutes'])
    device.pop('StaticRoutes', None)

iv_path = os.path.join(ws_path, 'traces/'+trace+'_invariants.yml')
with open(iv_path) as f:
    iv = yaml.load(f, Loader=yaml.SafeLoader)

# build name dict for devices and interfaces
device_dict = {
    device['Name']:device
    for device in cp['Devices']
}
interface_dict = {
    interface['Name']:interface
    for device in cp['Devices'] for interface in device['Interfaces']
}

# BGP state data structure: rib, init with advertised routes
"""rib stucture demo:
    r1:
      - Prefix: 1.1.1.1/32
        ASPath: [r2, r3]
        Interface: Eth1
        LocalPref: 100
      # locally originated routes
      - Prefix: 10.0.0.1/32
        ASPath: []
        Interface: None
        LocalPref: 100
    r2:
      - Prefix: 1.1.1.1/32
        ASPath: [r3]
        Interface: Eth2
        LocalPref: 100
"""
rib = {
    device['Name']:[]
    for device in cp['Devices'] 
}

# init RIB with advertised routes
for device in cp['Devices']:
    for prefix in device['BgpConfig'][0]['AdvertisedRoutes']:
        rib[device['Name']].append(rib_entry_init(prefix))

print(rib)



