import logging
import time
from xdevs import PHASE_ACTIVE, PHASE_PASSIVE, get_logger
from xdevs.models import Atomic, Coupled, Port

logger = get_logger(__name__, logging.DEBUG)

PHASE_DONE = "done"


class Job:
    def __init__(self, name: str):
        """
        Job event class. It represents a job sent by the generator and processed by the processor.
        :param name: job name
        """
        self.name: str = name
        self.time: float = 0
    def __str__(self):
        return self.name

class Generator(Atomic):
    def __init__(self, name: str, gen_t: float):
        """
        Generator model. It generates jobs at a given period.
        :param name: model name
        :param gen_t: period between job generations
        """
        super().__init__(name)

        if gen_t < 1:
            raise ValueError('gen_t must be greater than 0')

        self.i_stop: Port[bool] = Port(bool, "i_stop")
        self.o_job: Port[Job] = Port(Job, "o_out")

        self.add_in_port(self.i_stop)
        self.add_out_port(self.o_job)

        self.gen_t: float = gen_t
        self.job_counter: int = 1

    def initialize(self):
        self.hold_in(PHASE_ACTIVE, self.gen_t)

    def exit(self):
        pass

    def deltint(self):
        self.job_counter += 1
        self.hold_in(PHASE_ACTIVE, self.gen_t)

    def deltext(self, e):
        self.continuef(e)
        if self.i_stop.get():
            self.passivate()
        elif self.sigma == float('inf'):
            self.hold_in(PHASE_ACTIVE, self.gen_t)

    def lambdaf(self):
        self.o_job.add(Job(str(self.job_counter)))


class Processor(Atomic):
    def __init__(self, name: str, proc_t: float):
        """
        Processor model. It processes jobs with a given processing time.
        :param name: model name
        :param proc_t: processing time
        """
        super().__init__(name)

        if proc_t < 1:
            raise ValueError('proc_t must be greater than 0')

        self.i_in: Port[Job] = Port(Job, "i_in")
        self.o_out: Port[Job] = Port(Job, "o_out")

        self.add_in_port(self.i_in)
        self.add_out_port(self.o_out)

        self.current_job: Job | None = None
        self.proc_t: float = proc_t

    def initialize(self):
        self.passivate()

    def exit(self):
        pass

    def deltint(self):
        self.passivate()

    def deltext(self, e):
        if self.phase == PHASE_PASSIVE:
            self.current_job = self.i_in.get()
            self.hold_in(PHASE_ACTIVE, self.proc_t)
        else:
            self.continuef(e)

    def lambdaf(self):
        self.o_out.add(self.current_job)


class Transducer(Atomic):
    def __init__(self, name: str, obs_t: float):
        super().__init__(name)

        if obs_t < 0:
            raise ValueError('obs_t must be greater or equal than 0')

        self.i_arrived: Port[Job] = Port(Job, "i_arrived")
        self.i_solved: Port[Job] = Port(Job, "i_solved")
        self.o_out: Port[bool] = Port(bool, "o_out")

        self.add_in_port(self.i_arrived)
        self.add_in_port(self.i_solved)
        self.add_out_port(self.o_out)

        self.jobs_arrived: list[Job] = []
        self.jobs_solved: list[Job] = []

        self.total_ta: float = 0
        self.clock: float = 0
        self.obs_t: float = obs_t

    def initialize(self):
        self.hold_in(PHASE_ACTIVE, self.obs_t)

    def exit(self):
        pass

    def deltint(self):
        self.clock += self.sigma

        if self.phase == PHASE_ACTIVE:
            avg_ta = 0
            throughput = 0
            if self.jobs_solved:
                avg_ta = self.total_ta / len(self.jobs_solved)
                throughput = len(self.jobs_solved) / self.clock if self.clock > 0 else 0

            logger.info(f'End time: {self.clock}')
            logger.info(f'Jobs arrived: {len(self.jobs_arrived)}')
            logger.info(f'Jobs solved: {len(self.jobs_solved)}')
            logger.info(f'Average TA: {avg_ta}')
            logger.info(f'Throughput: {throughput}')

            self.hold_in(PHASE_DONE, 0)
        else:
            self.passivate()

    def deltext(self, e):
        self.clock += e

        if self.phase == PHASE_ACTIVE:
            if self.i_arrived:
                job = self.i_arrived.get()
                logger.info(f'Starting job {job.name} @ t = {self.clock} @ t = {time.time_ns()}')
                job.time = self.clock
                self.jobs_arrived.append(job)

            if self.i_solved:
                job = self.i_solved.get()
                logger.info(f'Job {job.name} finished @ t = {self.clock} @ t = {time.time()}')
                self.total_ta += self.clock - job.time
                self.jobs_solved.append(job)

        self.continuef(e)

    def lambdaf(self):
        if self.phase == PHASE_DONE:
            self.o_out.add(True)

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
class Gpt(Coupled):
    def __init__(self, name: str, gen_t: float, proc_t: float, obs_t: float):
        super().__init__(name)

        gen = Generator('generator', gen_t)
        proc = Processor('processor', proc_t)
        trans = Transducer('transducer', obs_t)

        self.add_component(gen)
        self.add_component(proc)
        self.add_component(trans)

        self.add_coupling(gen.o_job, proc.i_in)
        self.add_coupling(gen.o_job, trans.i_arrived)
        self.add_coupling(proc.o_out, trans.i_solved)
        self.add_coupling(trans.o_out, gen.i_stop)

class GptIHOH(Coupled):

    # Adaptation of the GPT DEVS model for injecting events via a new input port and for ejection of events via a new
    # output port.

    def __init__(self, name: str, gen_t: float, proc_t: float, obs_t: float):
        super().__init__(name)

        gen = Generator('generator', gen_t)
        proc = Processor('processor', proc_t)
        trans = Transducer('transducer', obs_t)

        # New input handler port
        self.ih_in = Port(Job, name='ih_in')
        self.add_in_port(self.ih_in)

        # New output handler port
        self.oh_out = Port(Job, name='ih_in')
        self.add_out_port(self.oh_out)

        self.add_component(gen)
        self.add_component(proc)
        self.add_component(trans)

        # New coupling for the input handler
        self.add_coupling(self.ih_in, proc.i_in)

        # New coupling for the output handler
        self.add_coupling(proc.o_out, self.oh_out)

        self.add_coupling(gen.o_job, proc.i_in)
        self.add_coupling(gen.o_job, trans.i_arrived)
        self.add_coupling(proc.o_out, trans.i_solved)
        self.add_coupling(trans.o_out, gen.i_stop)




