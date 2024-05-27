from abc import ABC
from xdevs.abc.handler import InputHandler


class BadDependenciesHandler(InputHandler, ABC):
    def __init__(self, **kwargs):
        """
        Template input handler for using when dependencies are not imported.
        :param str handler_type: transducer type.
        """
        super().__init__(**kwargs)
        raise ImportError(f'{kwargs.get('handler_type')} input handler specific dependencies are not imported')

    def run(self):
        pass
