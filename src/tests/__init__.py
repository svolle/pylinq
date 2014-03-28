import unittest
import sys
from os.path import dirname

sys.path.append('..')


def suite():
    test_loader = unittest.TestLoader()
    return test_loader.discover(dirname(__file__), '*.py')


def main():
    unittest.main(defaultTest='suite')

if __name__ == '__main__':
    main()
