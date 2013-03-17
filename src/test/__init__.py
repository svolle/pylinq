import unittest
from os.path import dirname

def suite():
    test_loader = unittest.TestLoader()
    return test_loader.discover(dirname(__file__), '*.py')

def main():
    unittest.main(defaultTest='suite')

if __name__ == '__main__':
    main()
