from xdevs.abc.handler import InputHandler


class CallableFunction(InputHandler):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.function = kwargs['function']
        self.args = kwargs.get('f_args', list())
        self.kwargs = kwargs.get('f_kwargs', dict())

    def run(self):
        self.function(self.queue, *self.args, **self.kwargs)
