import sys

from xdevs.rt import RealTimeCoordinator, RealTimeManager
from xdevs.factory import Components


if __name__ == '__main__':
    file_path = sys.argv[1] if len(sys.argv) > 1 else 'gpt.json'

    model = Components.from_json(file_path)
    """
    # Virtual simulation
    coord_v_sim = Coordinator(model)
    coord_v_sim.initialize()
    coord_v_sim.simulate()
    """
    # Wall-clock simulation
    m_rt = RealTimeManager(0.2,1)
    coord_rt_sim = RealTimeCoordinator(model, m_rt)
    coord_rt_sim.simulate_rt()

