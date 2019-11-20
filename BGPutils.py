import copy

# initiate to use global datastucture from main.py
def bgp_init(_rib, _cp, _device_dict, _in_policy_dict, _out_policy_dict):
    global rib, cp, device_dict, in_policy_dict, out_policy_dict
    rib = _rib
    cp = _cp
    device_dict = _device_dict
    in_policy_dict = _in_policy_dict
    out_policy_dict = _out_policy_dict

def rib_entry_init(prefix):
    return {
        'Prefix':prefix,
        'ASPath':[],
        'Tag': {},
        'Interface':None,
        'LocalPref':100
    }

def rib_entry_match(entry, matches):
    return

def rib_entry_action(entry, actions):
    return

def rib_entry_output(entry):
    return

def bgp_in(device_name, route_infos):
    return

def bgp_out(device_name):
    for interface in device_dict[device_name]['Interfaces']:
        if interface['Neighbor'] == None:
            continue
        neighbor_device_name = interface['Neighbor'].split('@')[0]
        if neighbor_device_name == device_name:
            continue

        message = []
        for entry in rib[device_name]:      
            # send bgp routing info message
            route_info = copy.deepcopy(entry)
            if interface['OutBgpPolicy'] != None:
                out_policy = out_policy_dict[interface['OutBgpPolicy']]
                for clause in out_policy['PolicyClauses']:
                    if rib_entry_match(route_info, clause['Matches']):
                        if not rib_entry_action(route_info, clause['Actions']):
                            continue # dropped
            rib_entry_output(route_info)
            message.append(route_info)

        bgp_in(neighbor_device_name, message)

def iterate_rib(order=[]):
    for device in order:
        bgp_out(device) 
    return

