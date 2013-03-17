import unittest

from pylinq.utils.observable import *

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
        
        