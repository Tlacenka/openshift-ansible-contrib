import argparse
import shade
import signal
import sys


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

    def AutoScaling(self):
        pass

    def gather_metrics(self):
        ''' Gathers metrics '''
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
        while True:
            pass


if __name__ == "__main__":

    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--interval', type=int, default=1)

    # Create and run an autoscaling service
    service = AutoScaling()
    service.run_prototype()
