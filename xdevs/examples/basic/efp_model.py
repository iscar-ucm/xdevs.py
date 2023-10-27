from xdevs.examples.basic.basic import Generator, Transducer, Job, Processor
from xdevs.models import Coupled, Port
from xdevs.sim import Coordinator


class EF(Coupled):
    def __init__(self, name, period, obs_time):
        super().__init__(name)

        if period < 1:
            raise ValueError("period has to be greater than 0")

        if obs_time < 0:
            raise ValueError("obs_time has to be greater or equal than 0")

        gen = Generator(name='EF_gen', period=period)
        trans = Transducer(name='EF_trans', obs_time=obs_time)

        self.add_component(gen)
        self.add_component(trans)

        self.p_in_ef = Port(Job, name='p_in_ef')
        self.p_out_ef = Port(Job, name='p_out_ef')

        self.add_in_port(self.p_in_ef)
        self.add_out_port(self.p_out_ef)

        self.add_coupling(gen.o_out, trans.i_arrived)
        self.add_coupling(gen.o_out, self.p_out_ef)
        self.add_coupling(trans.o_out, gen.i_stop)
        self.add_coupling(self.p_in_ef, trans.i_solved)


class EFP(Coupled):
    def __init__(self, name, period, obs_time, proc_time):
        super().__init__(name)

        ef = Ef(name='EF', period=period, obs_time=obs_time)

        proc = Processor(name='EFP_proc', proc_time=proc_time)

        self.add_component(ef)
        self.add_component(proc)

        self.add_coupling(ef.p_out_ef, proc.i_in)
        self.add_coupling(proc.o_out, ef.p_in_ef)


if __name__ == '__main__':

    EFP = EFP('efp', 3, 100, 5)
    Coord = Coordinator(EFP)
    Coord.initialize()
    Coord.simulate()
