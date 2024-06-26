from xdevs.sim import Coordinator
from xdevs.examples.gpt.models import Gpt

if __name__ == '__main__':

    gpt = Gpt("gpt", 3, 5, 100)
    coord = Coordinator(gpt)
    coord.initialize()
    coord.simulate()

