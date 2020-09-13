import unittest
from _queue import Empty
from Core.Bus import Bus
from Core.Event import Eventer, ServiceType, Receiver
from Core.Event.TestMsg import TestEvent


class TestBUS(unittest.TestCase):

    def setUp(self):
        self.bus = Bus()
        self.a = self.bus.getBusPort(Eventer("a", ServiceType.Bridge))
        self.b = self.bus.getBusPort(Eventer("b", ServiceType.Plugin))
        self.c = self.bus.getBusPort(Eventer("c", ServiceType.Plugin))
        self.bc = self.bus.getBusPort(Eventer("bc", ServiceType.Plugin))

    def tearDown(self) -> None:
        self.bus.close()

    def test_正常创建(self):
        testEvent = TestEvent()
        self.a.send(Receiver(Eventer("b", ServiceType.Plugin)), testEvent)
        msg = self.b.receive(timeout=0.1)
        self.assertEqual(msg.source, Eventer("a", ServiceType.Bridge))
        self.assertEqual(msg.payload, testEvent)

    def test_通配符测试(self):
        testEvent = TestEvent()
        self.a.send(Receiver(Eventer("*", ServiceType.Plugin)), testEvent)

        msg = self.b.receive(timeout=0.1)
        self.assertEqual(msg.source, Eventer("a", ServiceType.Bridge))
        self.assertEqual(msg.payload, testEvent)

        msg = self.c.receive(timeout=0.1)
        self.assertEqual(msg.source, Eventer("a", ServiceType.Bridge))
        self.assertEqual(msg.payload, testEvent)

        with self.assertRaises(Empty):  # a 不应该收到消息
            self.a.receive(timeout=0.1)


    def test_通配符测试2(self):
        testEvent = TestEvent()
        self.a.send(Receiver(Eventer("b*", ServiceType.Plugin)), testEvent)
        msg = self.b.receive(timeout=0.1)
        self.assertEqual(msg.source, Eventer("a", ServiceType.Bridge))
        self.assertEqual(msg.payload, testEvent)
        msg = self.bc.receive(timeout=0.1)
        self.assertEqual(msg.source, Eventer("a", ServiceType.Bridge))
        self.assertEqual(msg.payload, testEvent)
        with self.assertRaises(Empty):  # c 不应该收到消息
            self.c.receive(timeout=0.1)
        with self.assertRaises(Empty):  # a 不应该收到消息
            self.a.receive(timeout=0.1)


    def test_未匹配到的接收(self):
        testEvent = TestEvent()
        self.a.send(Receiver(Eventer("c", ServiceType.Plugin)), testEvent)
        with self.assertRaises(Empty):  # b 不应该收到消息
            self.b.receive(timeout=0.1)
        msg = self.c.receive(timeout=0.1)  # c 应该收到消息
        self.assertEqual(msg.source, Eventer("a", ServiceType.Bridge))
        self.assertEqual(msg.payload, testEvent)

    def test_错误的payload(self):
        with self.assertRaises(ValueError):
            self.a.send(Receiver(Eventer("b", ServiceType.Plugin)), object())
