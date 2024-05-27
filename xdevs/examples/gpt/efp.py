from xdevs.examples.gpt.gpt import Generator, Transducer, Job, Processor
from xdevs.models import Coupled, Port


class Ef(Coupled):
    def __init__(self, name: str, gen_t: float, obs_t: float):
        super().__init__(name)

        gen = Generator('generator', gen_t)
        trans = Transducer('transducer', obs_t)

        self.add_component(gen)
        self.add_component(trans)

        self.p_in_ef = Port(Job, name='p_in_ef')
        self.p_out_ef = Port(Job, name='p_out_ef')

        self.add_in_port(self.p_in_ef)
        self.add_out_port(self.p_out_ef)

        self.add_coupling(gen.o_job, trans.i_arrived)
        self.add_coupling(gen.o_job, self.p_out_ef)
        self.add_coupling(trans.o_out, gen.i_stop)
        self.add_coupling(self.p_in_ef, trans.i_solved)


class Efp(Coupled):
    def __init__(self, name: str, gen_t: float, proc_t: float, obs_t: float):
        super().__init__(name)

        ef = Ef('ef', gen_t, obs_t)
        proc = Processor('processor', proc_t)

        self.add_component(ef)
        self.add_component(proc)

        self.add_coupling(ef.p_out_ef, proc.i_in)
        self.add_coupling(proc.o_out, ef.p_in_ef)


if __name__ == '__main__':
    from xdevs.sim import Coordinator

    efp = Efp('efp', 3, 5, 100)
    coord = Coordinator(efp)
    coord.initialize()
    coord.simulate_iters()
