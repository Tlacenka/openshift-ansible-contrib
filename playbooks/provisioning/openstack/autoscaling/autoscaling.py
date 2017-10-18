import argparse
import os
import signal
import sys


from gnocchiclient.v1 import client
from keystoneauth1.identity import generic as keystone_id
from keystoneauth1 import session
import shade


# Handle SIGINT, SIGTERM
def handler(signum, frame):

    name= "SIGTERM" if signum == 15 else "SIGINT"
    print('\n{} received, closing program.'.format(name))
    sys.exit(0)

signal.signal(signal.SIGINT, handler)
signal.signal(signal.SIGTERM, handler)


class AutoScaling:
    ''' This class implements the autoscaling service.
        Its main method runs in the background, gathers metrics and triggers
        scaling events when certain limits are met. '''

    check_history = [False, False, False] # True = workload exceeded
    interval = 1 # in minutes, describes how often a check is performed
    gnocchi_session = None

    def __init__(self):
        # Connect to OpenStack with shade
        #self.shade_cloud = shade.openstack_cloud()
        # shade example
        #networks = self.shade_cloud.list_networks()
        #print(networks)

        # Connect to Gnocchi client
        auth = keystone_id.Password(auth_url=os.environ["OS_AUTH_URL"],
                                    username=os.environ["OS_USERNAME"],
                                    password=os.environ["OS_PASSWORD"],
                                    project_name=os.environ["OS_TENANT_NAME"])
        keystone_session = session.Session(auth=auth)
        self.gnocchi_session = client.Client(session=keystone_session)

        # Gnocchi Example
        self.gnocchi_session.metric.create({'name':'hello'})
        print(self.gnocchi_session.metric.list())


    # http://gnocchi.xyz/gnocchiclient/api.html#usage
    # https://github.com/openstack/tripleo-validations/blob/master/tripleo_validations/utils.py
       

    def gather_metrics(self):
        ''' Gathers metrics '''
        # https://github.com/redhat-openstack/openshift-on-openstack/blob/master/openshift.yaml#L804-L840
        pass

    def analyse_workload(self):
        ''' Run algorithm/check to determine whether scaling should be triggered.
            Store results (in this case, to check_history). '''

    def upscaling_required(self):
        ''' Based on analysis result, return whether scaling should be triggered.
            In this case, it is whenever workload exceeds limit 3 times in a row. '''

        return False

    def trigger_upscaling(self):
        ''' Perform upscaling.
            Make sure next scaling event starts after the current one is finished. '''
        pass

    def perform_check(self):
        ''' Gathers metrics,
            decides whether to trigger a scaling event
            (and does so if needed). '''

        self.gather_metrics()
        self.analyse_workload()

        if self.upscaling_required():
            self.trigger_upscaling()

    def run_prototype(self):
        ''' Perform checks every minute.
            If CPU workload exceeds 70% 3 times in a row, scale up by 1. '''
        pass


if __name__ == "__main__":

    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--interval', type=int, default=1)

    # Create and run an autoscaling service
    service = AutoScaling()
    service.run_prototype()
