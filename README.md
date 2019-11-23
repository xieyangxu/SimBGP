# SimBGP
A simple BGP simulator

## About
This project simulates BGP to produce a dataplane that is verified by tryAP.

## Dependencies and Installation
Python 3.7, pyyaml 5.1.2, pyeda 0.28.0

See tryAP for installation instructions.

## Usage
Run `python3 main.py <trace name>` where <trace name> is either `sample` or `bistable`.

## Key Components
`traces` contains the given networks and invariants. SimBGP produces dataplanes and tryAP queries and places them in this directory.

`FTUtils.py` converts RIBs to forwarding tables to generate the data plane.

`BGPUtils.py` contains the BGP simulation logic. `bgp_iterate` updates each node in the graph until the control plane no longer updates.

`main.py` processes command line args and yaml files, runs the BGP simulator, calls tryAP, and processes the routing rules.
