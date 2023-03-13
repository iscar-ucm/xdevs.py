import logging
import queue
import random
import time

from xdevs import PHASE_ACTIVE, PHASE_PASSIVE, get_logger
from xdevs.models import Atomic, Coupled, Port
from xdevs.rt_sim import RealTimeCoordinator, RealTimeManager

logger = get_logger(__name__, logging.INFO)

PHASE_DONE = "done"


class Job:
    def __init__(self, name):
        self.name = name
        self.time = 0


class Generator(Atomic):

    def __init__(self, name, period):
        super().__init__(name)
        self.i_start = Port(Job, "i_start")
        self.i_extern = Port(Job, "i_extern")  # receives additional jobs from outside
        self.i_stop = Port(Job, "i_stop")
        self.o_out = Port(Job, "o_out")

        self.add_in_port(self.i_start)
        self.add_in_port(self.i_stop)
        self.add_in_port(self.i_extern)
        self.add_out_port(self.o_out)

        self.period = period
        self.job_counter = 1
        self.extern_jobs = list()  # stores external jobs

    def initialize(self):
        self.hold_in(PHASE_ACTIVE, self.period)

    def exit(self):
        pass

    def deltint(self):
        self.job_counter += 1
        self.extern_jobs.clear()
        self.hold_in(PHASE_ACTIVE, self.period)

    def deltext(self, e):
        self.sigma -= e
        for msg in self.i_extern.values:
            logger.info("Generator received external job. It will forward it in the next lambda")
            self.extern_jobs.append(msg)
        if not self.i_stop.empty():
            self.passivate()

    def lambdaf(self):
        self.o_out.add(Job(str(self.job_counter)))
        for msg in self.extern_jobs:  # we also forward external messages
            self.o_out.add(msg)


class Processor(Atomic):
    def __init__(self, name, proc_time):
        super().__init__(name)

        self.i_in = Port(Job, "i_in")
        self.o_out = Port(Job, "o_out")

        self.add_in_port(self.i_in)
        self.add_out_port(self.o_out)

        self.current_job = None
        self.proc_time = proc_time

    def initialize(self):
        self.passivate()

    def exit(self):
        pass

    def deltint(self):
        self.passivate()

    def deltext(self, e):
        if self.phase == PHASE_PASSIVE:
            self.current_job = self.i_in.get()
            self.hold_in(PHASE_ACTIVE, self.proc_time)
        self.continuef(e)

    def lambdaf(self):
        self.o_out.add(self.current_job)


class Transducer(Atomic):

    def __init__(self, name, obs_time):
        super().__init__(name)

        self.i_arrived = Port(Job, "i_arrived")
        self.i_solved = Port(Job, "i_solved")
        self.o_out = Port(Job, "o_out")

        self.add_in_port(self.i_arrived)
        self.add_in_port(self.i_solved)
        self.add_out_port(self.o_out)

        self.jobs_arrived = []
        self.jobs_solved = []

        self.total_ta = 0
        self.clock = 0
        self.obs_time = obs_time

    def initialize(self):
        self.hold_in(PHASE_ACTIVE, self.obs_time)

    def exit(self):
        pass

    def deltint(self):
        self.clock += self.sigma

        if self.phase == PHASE_ACTIVE:
            if self.jobs_solved:
                avg_ta = self.total_ta / len(self.jobs_solved)
                throughput = len(self.jobs_solved) / self.clock if self.clock > 0 else 0
            else:
                avg_ta = 0
                throughput = 0

            logger.info("End time: %f" % self.clock)
            logger.info("Jobs arrived: %d" % len(self.jobs_arrived))
            logger.info("Jobs solved: %d" % len(self.jobs_solved))
            logger.info("Average TA: %f" % avg_ta)
            logger.info("Throughput: %f\n" % throughput)

            self.hold_in(PHASE_DONE, 0)
        else:
            self.passivate()

    def deltext(self, e):
        self.clock += e

        if self.phase == PHASE_ACTIVE:
            for job in self.i_arrived.values:
                logger.info("Starting job %s @ t = %d @ t_r = %f" % (job.name, self.clock, time.time()))
                job.time = self.clock
                self.jobs_arrived.append(job)

            if self.i_solved:
                job = self.i_solved.get()
                logger.info("Job %s finished @ t = %d @ t_r = %f" % (job.name, self.clock, time.time()))
                self.total_ta += self.clock - job.time
                self.jobs_solved.append(job)

        self.continuef(e)

    def lambdaf(self):
        if self.phase == PHASE_DONE:
            self.o_out.add(Job("null"))


class RTGpt(Coupled):
    def __init__(self, name, period, obs_time):
        super().__init__(name)

        if period < 1:
            raise ValueError("period has to be greater than 0")

        if obs_time < 0:
            raise ValueError("obs_time has to be greater or equal than 0")

        gen = Generator("generator", period)
        proc = Processor("processor", 3 * period)
        trans = Transducer("transducer", obs_time)

        self.add_component(gen)
        self.add_component(proc)
        self.add_component(trans)

        # new input port for receiving input events
        self.i_extern = Port(Job, "i_extern")
        self.add_in_port(self.i_extern)
        # new coupling for forwarding messages to generator
        self.add_coupling(self.i_extern, gen.i_extern)

        self.add_coupling(gen.o_out, proc.i_in)
        self.add_coupling(gen.o_out, trans.i_arrived)
        self.add_coupling(proc.o_out, trans.i_solved)
        self.add_coupling(trans.o_out, gen.i_stop)


def inject_messages(q: queue.SimpleQueue):
    i = -1
    while True:
        f = round(random.gauss(3, 0.6), 2)
        # f = 3
        time.sleep(f)  # duermo f segundos
        # la cola espera tuplas (port_name, msg)
        q.put(("i_extern", Job(i)))
        i -= 1
        # test ventana manager
        # time.sleep(0.3)
        # q.put(("i_extern", Job(i)))
        # i -= 1


if __name__ == '__main__':
    execution_time = 30
    time_scale = 1
    max_jitter = 0.2
    event_window = 0.5

    gpt = RTGpt("gpt", 2, 3600)

    manager = RealTimeManager(max_jitter=max_jitter, time_scale=time_scale, event_window=event_window)

    parsers = {
        'i_extern': lambda x: Job(int(x))  # le digo al input handler como convertir el string a Job con una función
    }
    manager.add_input_handler('csv_handler', file="prueba.csv", parsers=parsers)

    manager.add_input_handler('function', function=inject_messages)

    c = RealTimeCoordinator(gpt, manager)
    t_ini = time.time()
    print(f' >>> COMENZAMOS : {t_ini}')
    c.simulate(time_interv=execution_time)
    print(f' >>> FIN : {time.time()}')
    print(f' Tiempo a ejecutar (s) = {execution_time * time_scale}')
    print(f' Tiempo ejecutado (s) = {(time.time() - t_ini)}')
    print(f' Error (%) = '
          f'{((time.time() - t_ini - (execution_time * time_scale)) / (execution_time * time_scale)) * 100}')
