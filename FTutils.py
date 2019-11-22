import copy


def ft_entry_init(prefix=None, interface=None):
    return {
        'Prefix': prefix,
        'Interface': interface
    }

def ft_build_from_rib(rib, dp, device_dict_cp):
    for device in dp['Devices']:
        device_name = device['Name']
        rib_d = rib[device_name]

        # init forwarding table
        device['ForwardingTable'] = []
        ft = device['ForwardingTable']
        
        # translate static routes into fib entry
        for fi in device_dict_cp[device_name]['StaticRoutes']:
            ft.append(copy.deepcopy(fi))
        # translate rib entry into fib entry
        for prefix, entries in rib_d.items():
            for entry in entries:
                if len(entry['ASPath']) == 0:
                    # originated locally, added as static route
                    continue 
                # translate
                ft.append(ft_entry_init(prefix, entry['Interface']))
    