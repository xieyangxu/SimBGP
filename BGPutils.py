import copy
import re
import ipaddress

# initiate to use global datastucture from main.py


def bgp_init(_rib, _cp, _device_dict, _interface_dict, _policy_dict):
    
    global rib, cp
    global device_dict, interface_dict
    global policy_dict
    rib = _rib
    cp = _cp
    device_dict = _device_dict
    interface_dict = _interface_dict
    policy_dict = _policy_dict


def rib_entry_init(prefix):
    return {
        'Prefix': prefix,
        'ASPath': [],
        'Tag': set(),
        'Interface': None,
        'LocalPref': 100
    }


def prefix_match(entry_prefix, match_prefix_range):
    """implements prefix range matching in BGP policy
        the syntax 70.4.194.0/[24-32] matches a prefix with the first 24
        bits of 70.4.194.__ and a prefix length between 24 and 32.

        Returns:
            bool
    """
    entry_ipp = ipaddress.ip_network(entry_prefix)
    entry_ipa = entry_ipp.network_address
    entry_prefixlen = entry_ipp.prefixlen
    mask = int(entry_ipp.netmask)

    ip_prefix, low_range, high_range = \
        re.split("/\[|-|\]", match_prefix_range)[:-1]
    match_ipa = ipaddress.ip_address(ip_prefix)
    match_prefixlen_lbound = int(low_range)
    match_prefixlen_ubound = int(high_range)
    
    res = (int(entry_ipa) & mask) == (int(match_ipa) & mask)
    res &= entry_prefixlen >= match_prefixlen_lbound
    res &= entry_prefixlen <= match_prefixlen_ubound
    return res

def rib_entry_match(entry, kind, arg):
    if kind == "prefix":
        return prefix_match(entry['Prefix'], arg)
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


def rib_entry_to_message_entry(entry, device_name):
    """reformat rib entry to BGP message entry

        demo input (RIB entry):
            - Prefix: 1.1.1.1/32
              ASPath: [r2, r3]
              Tag: {1, 7}
              Interface: r1@Eth1
              LocalPref: 100
        demo output (BGP message entry):
            - Prefix: 1.1.1.1/32
              ASPath: [r1, r2, r3]
              Tag: {1, 7}
    """
    entry.pop('Interface')
    entry.pop('LocalPref')
    entry['ASPath'].insert(0, device_name)

def message_entry_to_rib_entry(entry, interface_name):
    entry['Interface'] = interface_name
    entry['LocalPref'] = 100


def apply_policy_on_rib_entry(clauses, entry):
    """apply a list of match-actions on an entry (RIB entry format)
        and make filter dicision
        
        May modify the entry according to match-actions
        Returns:
            ALLOW or DROP
    """
    res = None
    for clause in clauses:
        if rib_entry_matches(entry, clause['Matches']):
            res = rib_entry_actions(entry, clause['Actions'])
            if res == ALLOW:
                break
            elif res == PASS:
                continue
            elif res == DROP:
                break
            else:
                raise Exception(
                    f"Expected ALLOW, PASS, or DROP. Got {res}")
    if not (res == ALLOW or res == DROP):
        raise Exception("No ALLOW/DROP decision made")
    return res


def bgp_in(interface_name, message):
    device_name = interface_name.split('@')[0]
    interface = interface_dict[interface_name]

    for entry_in in message:
        entry_new = copy.deepcopy(entry_in)
        message_entry_to_rib_entry(entry_new, interface_name)
        if interface['InBgpPolicy'] != None:
            in_policy = policy_dict[interface['InBgpPolicy']]
            res = apply_policy_on_rib_entry(
                in_policy['PolicyClauses'], entry_new)
            if res == DROP:
                continue
        # avoid loop
        for device in entry_new['ASPath']:
            if device == device_name:
                continue
        rib[device_name].append(entry_new)



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
            entry_out = copy.deepcopy(entry)
            if interface['OutBgpPolicy'] != None:
                out_policy = policy_dict[interface['OutBgpPolicy']]
                res = apply_policy_on_rib_entry(
                    out_policy['PolicyClauses'], entry_out)
                if res == DROP:
                    continue
            message.append(entry_out)

        for entry_out in message:
            rib_entry_to_message_entry(entry_out, device_name)
        bgp_in(interface['Neighbor'], message)


def iterate_rib(order=[]):
    for device in order:
        bgp_out(device)
    return
