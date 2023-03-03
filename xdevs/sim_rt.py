from __future__ import annotations

import _thread
import itertools
import pickle
import logging
import threading
import queue
import time as rt_time

from abc import ABC, abstractmethod
from collections import defaultdict
from concurrent import futures
from typing import Callable, Generator
from xmlrpc.server import SimpleXMLRPCServer

from xdevs import INFINITY
from xdevs.models import Atomic, Coupled, Component, Port, T
from xdevs.sim import AbstractSimulator, Coordinator
from xdevs.transducers import Transducer


class CoordinatorRt(Coordinator):

    def __init__(self, model: Coupled, time_scale: float, max_delay: float):
        super().__init__(model)

        self.time_scale = time_scale
        self.max_delay = max_delay

    def simulate(self, time_interv : float = 10000):
        """
        Simulates the behavior of a DEVS model in real time over a specified time interval.

        :param time_interv: The time interval to simulate, in seconds. Default is 10000.
        """
        self.clock.time = 0
        tf = self.clock.time + time_interv

        t_before = rt_time.time()  # real time before executing lambdas and deltas
        t_after = t_before  # real time after executing lambdas and deltas
        total_delayed_t = 0.0  # delay compensation buffer

        while self.clock.time < tf:
            if self.time_next == float("inf"):
                print("infinity reached and no event handler configured")
                break
            # FIRST WE COMPUTE SLEEP TIME
            v_sleep = (self.time_next - self.clock.time)  # virtual sleep time
            r_sleep = v_sleep * self.time_scale - (t_after - t_before) - total_delayed_t  # real sleep time
            # THEN WE CHECK THAT DELAY IS NOT TOO BAD
            if r_sleep < 0:
                total_delayed_t = -r_sleep
                if total_delayed_t > self.max_delay:  # too much delay -> stop execution
                    raise RuntimeError('ERROR: to much delayed time ')
            else:  # Sleep is positive. time elapsed and delayed_time are small. Everything went well
                total_delayed_t = 0
                rt_time.sleep(r_sleep)
                t_before = rt_time.time()
                v_sleep = min(v_sleep, (t_before - t_after) / self.time_scale)
            # TIME TO SLEEP
            # UPDATE SIMULATION CLOCK AND STORE TIME BEFORE NEXT CYCLE
            self.clock.time += v_sleep
            # EXECUTE NEXT CYCLE
            if self.clock.time == self.time_next:  # now lambdas are optional
                self.lambdaf()
            self.deltfcn()
            self._execute_transducers()
            self.clear()
            # STORE TIME AFTER THE CYCLE
            t_after = rt_time.time()  # time after executing lambdas and deltas
        print("done")
