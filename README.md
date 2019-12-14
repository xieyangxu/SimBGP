# SimBGP
BGP simulator with link failure reasoning

## About
This tool takes a controlplane file and reachability queries as input. It reasons about the controlplane behavior under all possible link failure conditions. The query judging decides whether the (src, dst) pair is robustly reachable given a maximum number of failed links.
The tool uses underlying controlplane test tool and dataplane test tools.

## Installation and Usage
Python 3.7, pyyaml 5.1.2, pyeda 0.28.0

1. Install dependencies

   Make sure python version is 3.7

   Use ./Pipfile for pipenv

   or

   `pip3 install pyyaml`

   `pip3 install pyeda`

2. Clone project
   `git clone --recursive https://github.com/Ashlippers/SimBGP.git`

3. Checkout to failure reasoning branch
   `git checkout failure_reasoning`

4. Run sample trace

   `python3 main.py`


## Key Components
`traces` contains the given networks and invariants. SimBGP produces dataplanes and tryAP queries and places them in this directory.

`FTUtils.py` converts RIBs to forwarding tables to generate the data plane.

`BGPUtils.py` contains the BGP simulation logic. `bgp_iterate` updates each node in the graph until the control plane no longer updates.

`main.py` processes command line args and yaml files, runs the BGP simulator, calls tryAP, and processes the routing rules.
