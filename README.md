# SimBGP
BGP simulator with link failure reasoning

## About
This project simulates BGP to produce dataplanes that are verified by tryAP.

SimBGP takes as input a control plane file and reachability queries. Each reachability query asks
SimBGP whether a set of packets can move from a given source to a given destination subject to at
most `MaxFailures` link failures.

SimBGP accomplishes this by testing all combinations of link failures up to
the specified `MaxFailures`, generating corresponding dataplanes for each one, and giving those dataplanes to
the dataplane verifier tryAP. This approach is straightforward, but slow.
State-of-the-art approaches use techniques from areas like abstract interpretation, synthesis, deep
learning, and constraint solving to more quickly find link failures that lead to invariant
violations. Those tools exploit domain-specific knowledge to prune, simplify, and guide search.

In more detail, SimBGP handles link failures by adding an `FailFlag` field to the internal
representation of interfaces. If this flag is `True` then the interface (and thus its corresponding
link) is considered down and the simulator ignores that interface. Combinations of down links are
enumerated with the help of the `itertools.combinations` function.

## Installation and Usage
Depencencies: Python 3.7, pyyaml 5.1.2, pyeda 0.28.0

1. Install dependencies

   Make sure python version is 3.7

   `pip3 install pyyaml`

   `pip3 install pyeda`

2. Clone project

   `git clone --recursive https://github.com/Ashlippers/SimBGP.git`

3. Checkout to failure reasoning branch

   `git checkout failure_reasoning`

4. Run sample trace

   `python3 main.py`

To specify your own trace, add a network yaml, `<trace name>_network.yml`, to the
`traces/network` directory; add an invariants yaml, `<trace name>_invariants.yml`, to the
`traces/invariants` directory; and set `trace` to `<trace name>` in `main.py`.

## Key Components
`traces` contains the given networks and invariants. SimBGP produces dataplanes and tryAP queries
and places them in the `dataplane` and `query` subdirectories, respectively.

`FTUtils.py` converts RIBs to forwarding tables to generate the data plane.

`BGPUtils.py` contains the BGP simulation logic. `bgp_iterate` updates each node in the graph until the control plane no longer updates.

`main.py` processes command line args and yaml files, `cp_failure_reasoning` checks a reachability query with maximum failures by emumerate all failure cases and check each of them with underlying `cp_check`. `cp_check` runs the BGP simulator to build up a dataplane of its converged state, and calls tryAP to check reachability in dataplane.
