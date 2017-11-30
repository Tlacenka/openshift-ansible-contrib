#!/usr/bin/python

"""This module contains a class for auto-scaling prototype.

It scales application nodes in the OpenShift on OpenStack environment.
"""


import argparse
import logging
import os
import signal
from subprocess import call
import sys
import time


from gnocchiclient.v1 import client
from keystoneauth1.identity import generic as keystone_id
from keystoneauth1 import session
import shade


# Global variables
alarm_interval = 60


# Exception for alarm handling
class SIGALRM(Exception):
    """Exception used when alarm has been activated."""

    pass


# Exception for scaling error handling
class ScalingFailed(Exception):
    """Exception used when scaling has failed."""

    pass


# Handle SIGALRM
def handler(signum, frame):
    """Handle the SIGALRM."""
    signal.alarm(alarm_interval)
    raise SIGALRM("Start another check")

signal.signal(signal.SIGALRM, handler)


# Main autoscaling class
class AutoScaling:
    """This class implements the autoscaling service.

    Its main method runs in the background, gathers metrics and triggers
    scaling events when certain limits are met.
    """

    def __init__(self, inventory_path, openshift_ansible_path, upscaling_path):
        """Class instance initialization.

        Attributes are set, OpenStack authentication is performed.
        """
        # Set attributes
        self.check_history = [False, False, False]  # True = workload exceeded
        self.index = 0
        self.increment_by = 1
        self.inventory_path = inventory_path
        self.openshift_ansible_path = openshift_ansible_path
        self.upscaling_path = upscaling_path

        # shade example
        # self.shade_cloud = shade.openstack_cloud()
        # networks = self.shade_cloud.list_networks()
        # logging.debug(networks)

        # Connect to Gnocchi client
        auth = keystone_id.Password(auth_url=os.environ['OS_AUTH_URL'],
                                    username=os.environ['OS_USERNAME'],
                                    password=os.environ['OS_PASSWORD'],
                                    project_name=os.environ['OS_TENANT_NAME'])
        keystone_session = session.Session(auth=auth)
        self.gnocchi_session = client.Client(session=keystone_session)

        # Gnocchi Example
        # Create a metric
        #cpu_util_id = self.gnocchi_session.metric.create(
        #              {'name': 'cpu_util'})['id']

        # List all available metrics
        #logging.debug(self.gnocchi_session.metric.list())

        # List all resources
        #logging.debug(self.gnocchi_session.resource.list())
        resources = self.gnocchi_session.resource.list()
        
        # For each resource, get its cpu_util metric
        #for r in resources:
        #    logging.debug(r['id'])
        #    logging.debug(self.gnocchi_session.get('cpu_util', r['id']))

        # For each resource, display the metric values
        for r in resources:
            print('Resource ' + r['id'] + ':\n')
            try:
                logging.debug(self.gnocchi_session.metric.get_measures('cpu_util', resource_id=r['id']))
            except Exception:
                print('This resource does not have any metric.')

        # Get last x values from it and decide whether to scale
        # it is [timestamp, granularity, value]

        # Delete the metric
        #self.gnocchi_session.metric.delete(cpu_util_id)

        logging.debug('Setting first alarm')
        signal.alarm(alarm_interval)

    def gather_metrics(self):
        """Gather metrics."""
        # https://github.com/redhat-openstack/openshift-on-openstack/blob/master/openshift.yaml#L804-L840
        pass

    def analyse_workload(self):
        """Run algorithm/check to determine whether scaling should be triggered.

        Store results (in this case, to check_history).
        """
        self.check_history[self.index] = True
        self.index = (self.index + 1) % len(self.check_history)

    def upscaling_required(self):
        """Based on analysis result, return whether scaling should be triggered.

        In this case, whenever workload exceeds limit 3 times in a row.
        """
        return all(self.check_history)

    def trigger_upscaling(self):
        """Perform upscaling.

        Make sure that the next scaling event starts after the current one
        is finished.
        For now, alarm is reset after scaling is done to prevent
        alarm going off while scaling is in progress.
        """
        try:
            logging.debug('Stopping alarm')
            signal.alarm(0)

            # Scaling process
            with open('tmp.out', 'w') as fp:
                retval = call(['ansible-playbook', '-i', self.inventory_path,
                               '-e', 'increment_by=' + str(self.increment_by),
                               self.upscaling_path], stdout=fp, stderr=fp)

                # Then post-validation - tweak this
                # https://github.com/openshift/openshift-ansible-contrib/blob/master/ci/openstack/validate.sh

            # Check if it succeeded
            if retval:
                raise ScalingFailed
            else:
                # Reset the check history
                self.check_history[:] = [False] * len(self.check_history)

            logging.debug('Upscaling ended. Resetting alarm.')
            signal.alarm(alarm_interval)
        except KeyboardInterrupt:
            raise

    def perform_check(self):
        """Perform regular check.

        Gathers metrics, decides whether to trigger a scaling event
        (and does so if needed).
        """
        try_again = True

        while try_again:
            try:
                self.gather_metrics()
                self.analyse_workload()

                logging.debug('Decision making')

                if self.upscaling_required():
                    logging.debug('Upscaling started')
                    self.trigger_upscaling()

                logging.debug('End of check')
                try_again = False
            except SIGALRM:
                logging.debug('Check lasted more than expected. Restarting.')
            except (KeyboardInterrupt, ScalingFailed):
                raise

    def run_prototype(self):
        """Perform checks every minute.

        If CPU workload exceeds 70% 3 times in a row, scale up by 1.
        """
        while True:
            logging.debug('Running prototype')

            try:
                while True:
                    time.sleep(1)
            except SIGALRM:
                logging.debug('run_prototype: SIGALRM')
                self.perform_check()
            except (KeyboardInterrupt, ScalingFailed):
                raise


if __name__ == '__main__':

    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--interval', type=int, default=1,
                        help='Interval between checks (1 min by default).')
    parser.add_argument('--inventory-path', type=str, default='inventory',
                        help='Path to ansible inventory.')
    parser.add_argument('--openshift-ansible-path', type=str,
                        default='openshift-ansible',
                        help='Path to openshift-ansible repository.')
    parser.add_argument('--upscaling-path', type=str,
                        default='openshift-ansible-contrib/playbooks/provisioning/openstack/scale-up.yaml',
                        help='Path to upscaling playbook.')
    parser.add_argument('--debug', action='store_true',
                        help='When set, debug output is printed out.')
    args = parser.parse_args()

    # Set alarm interval
    alarm_interval = int(args.interval) * 60

    # Create a logging object, set threshold for logging severity
    debug_lvl = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=debug_lvl,
                        format='%(asctime)s %(levelname)s: %(message)s')

    # Create and run an autoscaling service
    service = AutoScaling(args.inventory_path, args.openshift_ansible_path,
                          args.upscaling_path)

    logging.info('Auto-scaling service is starting.' +
                 'In order to stop this service in a clean manner, ' +
                 'press Ctrl+C.')
    try:
        service.run_prototype()
    except KeyboardInterrupt:
        logging.info('SIGINT received, ending run.')
        sys.exit(0)
    except ScalingFailed:
        logging.error('Upscaling failed. For more info, open tmp.out')
        sys.exit(1)


# Sources, documentation:
# So get all app nodes, their ids, collect metrics from all and get avg?
# http://gnocchi.xyz/gnocchiclient/api.html#usage
# https://github.com/openstack/tripleo-validations/blob/master/tripleo_validations/utils.py
# http://aalvarez.me/blog/posts/understanding-gnocchi-measures.html
# http://gnocchi.xyz/gnocchiclient/api/gnocchiclient.v1.metric.html
# https://julien.danjou.info/blog/2015/openstack-gnocchi-first-release
