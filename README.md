# SimBGP
A simple BGP simulator

## About
This project simulates BGP to produce dataplanes that are verified by tryAP.

This version also reasons about failures. SimBGP accomplishes this by enumerating link failures in
the control plane up to the specified MaxFailures for a given Reachability query. This approach is
straightforward, but slow. A better approach is to use techniques from areas like synthesis, deep
learning, and constraint solving to more quickly find link failures that lead to invariant
violations. Such approaches should exploit domain-specific knowledge to prune, simplify, and guide search.

## Dependencies and Installation
Python 3.7, pyyaml 5.1.2, pyeda 0.28.0

See tryAP for installation instructions.

## Usage
Run `python3 main.py <trace name>`.  The example `<trace name>` is `netv`; however, you can
specify your own trace by adding a network yaml, `<trace name>_network.yml`, to the
`traces/network` directory; an invariants yaml, `<trace name>_invariants.yml`, to the
`traces/invariants` directory; and changing `trace` in `main.py`.

## Key Components
`traces` contains the given networks and invariants. SimBGP produces dataplanes and tryAP queries
and places them in the `dataplane` and `query` subdirectories, respectively.

`FTUtils.py` converts RIBs to forwarding tables to generate the data plane.

`BGPUtils.py` contains the BGP simulation logic. `bgp_iterate` updates each node in the graph until the control plane no longer updates.

`main.py` processes command line args and yaml files, runs the BGP simulator, calls tryAP, and processes the routing rules.
