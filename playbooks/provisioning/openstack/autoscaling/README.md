# Auto-Scaling Prototype

Bear in mind that this is still a work in progress.

## Introduction
This script runs the auto-scaling service that regularly monitors the target instances and
scales them up/down when required.

Its checking procedure consists of:
1. Gathering metrics about the monitored instances during the last period.
2. Storing metrics into a database/variable in the program.
3. Based on the metrics history, deciding whether to scale up/down.
4. If needed, triggering the corresponding scaling procedure and checking that it was successful.

The checks are invoked by `SIGALRM` signal every `N` minutes, raising a `SIGALRM`
exception that calls the `perform_check()` method and resets the alarm. By doing so,
it is easier to track how much time the check takes.
If a check that does not involve scaling takes longer than one period
(potentially due to a slower network connection), it is restarted.
Because scaling can take longer than one period, the alarm is stopped during
scaling and reset after the process has sucessfully finished.

## Usage

**Running the script**:

```
python <path>/autoscaling.py [--debug] [--interval MIN] [--inventory-path PATH]
       [--openshift-ansible-path PATH] [--upscaling-path PATH] [-h/--help]
```

The script can be exited at any time after initialization by sending the `SIGINT` to the
script (pressing `Ctrl+C`).

**Arguments**:
* `--debug` enables logging for debug messages
* `--interval MIN` sets period for one scaling iteration (1 minute by default)
* `--inventory-path PATH` sets path to your ansible inventory (*'inventory'* by default)
* `--openshift-ansible-path PATH` sets path to `openshift-ansible` directory (*'openshift-ansible'* by default)
* `--upscaling-path PATH` sets path to the upscaling playbook (*'openshift-ansible-contrib/playbooks/provisioning/openstack/scale-up.yaml'* by default)
