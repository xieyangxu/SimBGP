import copy
import re

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
        'Prefix': prefix,
        'ASPath': [],
        'Tag': set(),
        'Interface': None,
        'LocalPref': 100
    }


def rib_entry_match(entry, kind, arg):
    if kind == "prefix":
        ip_prefix, low_range, high_range = re.split("/\[|-|\]", arg)[:-1]
        entry_prefix, entry_range = entry["Prefix"].split("/", 1)
        low_range, entry_range, high_range = int(
            low_range), int(entry_range), int(high_range)
        return (ip_prefix == entry_prefix) and (low_range <= entry_range) and (entry_range <= high_range)
    elif kind == "neighbor":
        return not len(entry["ASPath"]) == 0 and entry["ASPath"][0] == arg
    elif kind == "tag":
        return arg in entry["Tag"]
    else:
        raise Exception(f"unknown match type: {kind}")


def rib_entry_matches(entry, matches):
    output = True
    for match in matches:
        output = output and rib_entry_match(entry, *match.split(": ", 1))
    return output


ALLOW = 1
PASS = 0
DROP = -1


def rib_entry_action(entry, action):
    action_name, *action_args = action.split(" ")
    if action_name == "allow":
        return ALLOW
    elif action_name == "drop":
        return DROP
    elif action_name == "add":
        if action_args[0] == "tag":
            entry["Tag"].add(action_args[1])
        else:
            raise Exception(f"Unexpected add: {action_args}")
        return PASS
    elif action_name == "remove":
        if action_args[0] == "tag":
            entry["Tag"].remove(action_args[1])
        else:
            raise Exception(f"Unexpected remove: {action_args}")
        return PASS
    elif action_name == "set":
        if action_args[0] == "localpref":
            entry["LocalPref"] = int(action_args[1])
        else:
            raise Exception(f"Unexpected set: {action_args}")
    else:
        raise Exception(f"Unexpected action: {action_name} {action_args}")


def rib_entry_actions(entry, actions):
    for action in actions:
        res = rib_entry_action(entry, action)
        if res == ALLOW or res == DROP:
            return res
    return PASS


def rib_entry_output(entry):
    pass


def bgp_in(device_name, route_infos):
    pass


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
                    if rib_entry_matches(route_info, clause['Matches']):
                        res = rib_entry_actions(route_info, clause['Actions'])
                        if res == ALLOW:
                            rib_entry_output(route_info)
                            message.append(route_info)
                            break
                        elif res == PASS:
                            continue
                        elif res == DROP:
                            break
                        else:
                            raise Exception(
                                f"Expected ALLOW, PASS, or DROP. Got {res}")

        bgp_in(neighbor_device_name, message)


def iterate_rib(order=[]):
    for device in order:
        bgp_out(device)
    return
