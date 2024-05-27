from __future__ import annotations
from abc import ABC
from xdevs.abc.transducer import Transducer


class BadDependenciesTransducer(Transducer, ABC):
    def __init__(self, **kwargs):
        """
        Template transducer for using when dependencies are not imported.
        :param str transducer_type: transducer type.
        """
        super().__init__(**kwargs)
        transducer_type = kwargs['transducer_type']
        raise ImportError(f'{transducer_type} transducer specific dependencies are not imported')

    def create_known_data_types_map(self):
        pass

    def initialize(self):
        pass

    def exit(self):
        pass

    def bulk_data(self, sim_time: float):
        pass
