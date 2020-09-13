import unittest,sys,os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from testBUS import TestBUS
from testCommand import testCommand
from testService import testService

if __name__ == '__main__':
    unittest.main()