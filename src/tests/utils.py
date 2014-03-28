import unittest

from pylinq.utils.observable import *
from mock import Mock

class ObservableTestCase(unittest.TestCase):
    def setUp(self):
        self.observable = Observable()
    
    def test_add_events(self):
        events_list = ['parrot', 'spam', 'spanish inquisition']
        self.observable.add_events(*events_list)
        
        events = self.observable.get_events()
        self.assertIsInstance(events, list)
        self.assertEqual(sorted(events), sorted(events_list))
        
    def test_has_event(self):
        self.observable.add_events('spam', 'eggs')
        
        self.assertTrue(self.observable.has_event('spam'))
        self.assertTrue(self.observable.has_event('eggs'))
        self.assertFalse(self.observable.has_event('foobar'))
        
    def test_bind_event(self):
        self.observable.add_events('spam')
        def foo():
            pass
        
        bogus = ()
        
        self.observable.bind('spam', foo)
        self.assertRaises(UnsupportedEventException, self.observable.bind, 'bogus', foo)
        self.assertRaises(HandlerMustBeCallableException, self.observable.bind, 'spam', bogus)
        
    def test_trigger_event(self):
        self.observable.add_events('spam')
        witness1 = [False]
        witness2 = [False]
        def foo(arg1, arg2):
            self.assertEqual(arg1, 'foobar')
            arg2[0] = True
            
        def bogus(arg):
            arg[0] = True
        
        self.observable.bind('spam', foo, 'foobar', witness1)
        self.observable.bind('spam', bogus, witness2)
        self.observable.trigger('spam')
        
        self.assertEqual(witness1[0], True)
        self.assertEqual(witness2[0], True)
        
    def test_unbind_event_handler(self):
        self.observable.add_events('spam')
        
        class Foo(object):
            def bar(self):
                pass
        
        foo = Foo()
        foo.bar = Mock()
        
        self.observable.bind('spam', foo.bar)
        self.observable.trigger('spam')
        
        self.assertTrue(foo.bar.called)
        
        self.observable.unbind('spam', foo.bar)
        self.observable.trigger('spam')
        
        self.assertEqual(foo.bar.call_count, 1)
        
    def test_unbind_all_event_handlers(self):
        self.observable.add_events('spam')
        
        class Foo(object):
            def bar(self):
                pass
            def baz(self):
                pass
        
        foo = Foo()
        foo.bar = Mock()
        foo.baz = Mock()
        
        self.observable.bind('spam', foo.bar)
        self.observable.bind('spam', foo.baz)
        self.observable.trigger('spam')
        
        self.assertEqual(foo.bar.call_count, 1)
        self.assertEqual(foo.bar.call_count, 1)
        
        self.observable.unbind('spam')
        self.observable.trigger('spam')
        
        self.assertEqual(foo.bar.call_count, 1)
        self.assertEqual(foo.baz.call_count, 1)