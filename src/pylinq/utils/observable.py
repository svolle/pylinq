class UnsupportedEventException(Exception):
    pass


class HandlerMustBeCallableException(Exception):
    pass


def must_have_event(func):
    def decorated(observable, event_name, *args,  **kwargs):
        if event_name not in observable.events:
            raise UnsupportedEventException(
                'This observable does not support event "%s"' % event_name)
        return func(observable, event_name, *args,  **kwargs)
    return decorated


class Observable(object):
    def __init__(self):
        self.events = dict()

    def add_events(self, *events):
        self.events = dict((event, {}) for event in events)

    def has_event(self, event):
        return event in self.events

    def get_events(self):
        return self.events.keys()

    @must_have_event
    def bind(self, event_name, event_handler, *args):
        if not callable(event_handler):
            raise HandlerMustBeCallableException(
                'Event handler must be callable')
        self.events[event_name][event_handler] = args

    @must_have_event
    def unbind(self, event_name, event_handler=None):
        if event_handler is None:
            self.events[event_name].clear()
        elif event_handler in self.events[event_name].keys():
            del self.events[event_name][event_handler]

    @must_have_event
    def trigger(self, event_name, *args):
        listeners = self.events[event_name]
        for handler, extra_args in listeners.items():
            all_args = args + extra_args
            handler(*all_args)
