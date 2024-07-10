from xdevs.rt import RealTimeCoordinator, RealTimeManager
from xdevs.examples.gpt.models import GptIHOH, Job

if __name__ == '__main__':
    gpt = GptIHOH("gpt", 20, 1, 100)
    manager = RealTimeManager(max_jitter=0.02,time_scale=1,event_window=.05)

    # The InputHandler under study will be a TCP one
    # msg_parser: How must the arrived messages adapt to the system, in this case they are converted into Jobs named
    # after the receiving message
    msg_parser = {"ih_in" : lambda x : Job(str(x))}
    # We pass the identifier and the required arguments for the TCP handler
    manager.add_input_handler("tcp", port=4321, msg_parsers=msg_parser)

    manager.add_output_handler('tcp', port=1234)

    coord = RealTimeCoordinator(gpt, manager)
    coord.simulate_rt()