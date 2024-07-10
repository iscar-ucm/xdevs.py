from xdevs.rt import RealTimeCoordinator, RealTimeManager
from xdevs.examples.gpt.models import Gpt

if __name__ == '__main__':
    gpt = Gpt("gpt", 2, 7, 100)
    manager = RealTimeManager(0.02,1,0.05)
    coordinator = RealTimeCoordinator(gpt, manager)
    coordinator.simulate_rt(100)
