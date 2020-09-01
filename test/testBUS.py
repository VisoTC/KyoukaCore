import unittest
from _queue import Empty
from Core.bus import BUS
from Core.Event import Eventer,EventerType,Receiver
from Core.Event.TestMsg import TestEvent
class TestBUS(unittest.TestCase):

    def setUp(self):
        self.bus = BUS()
        self.a = self.bus.getBusPort(Eventer("a",EventerType.Bridge))
        self.b = self.bus.getBusPort(Eventer("b",EventerType.Plugin))

    def test_正常创建(self):

        testEvent = TestEvent()
        self.a.send(Receiver(Eventer("b",EventerType.Plugin)),testEvent)
        msg = self.b.receive(timeout=1)
        self.assertEqual(msg.source, Eventer("a",EventerType.Bridge))
        self.assertEqual(msg.payload, testEvent)

    def test_错误的接收地址(self):

        testEvent = TestEvent()
        self.a.send(Receiver(Eventer("c",EventerType.Plugin)),testEvent)
        with self.assertRaises(Empty):
            self.b.receive(timeout=1)