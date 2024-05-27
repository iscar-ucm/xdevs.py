import sys
from xdevs.sim import Coordinator
from xdevs.factory import Components


if __name__ == '__main__':
    file_path = sys.argv[1] if len(sys.argv) > 1 else 'gpt.json'

    component = Components.from_json(file_path)
    coord = Coordinator(component)
    coord.initialize()
    coord.simulate_iters()
