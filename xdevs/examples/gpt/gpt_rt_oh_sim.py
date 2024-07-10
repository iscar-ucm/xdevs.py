from xdevs.rt import RealTimeCoordinator, RealTimeManager
from xdevs.examples.gpt.models import GptIHOH, Job

if __name__ == '__main__':
    gpt = GptIHOH("gpt", 5, 3, 100)
    manager = RealTimeManager(max_jitter=0.02,time_scale=1,event_window=.05)

    manager.add_output_handler('tcp',port=4321)

    coord = RealTimeCoordinator(gpt, manager)
    coord.simulate_rt()

