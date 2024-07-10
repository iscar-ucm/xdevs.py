from xdevs.sim import Coordinator
from xdevs.examples.gpt.models import Efp

if __name__ == '__main__':

    efp = Efp('efp', 3, 5, 100)
    coord = Coordinator(efp)
    coord.initialize()
    coord.simulate()
