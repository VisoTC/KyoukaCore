import unittest
from Core.Event import ReceiveEvent, Eventer, ServiceType, EventPayloadBase
from Core.Event.MsgEvent import MsgEvent
from Core.Event.MsgEvent.MsgContent import MsgContent, TextMsg
from Core.Event.MsgEvent.MsgInfo import GroupMsgInfo, PrivateMsgInfo
from Core.Service.Command import Command, FuncAttr
from Core.Service.exception import *


class testCommand(unittest.TestCase):

    def setUp(self):
        self.callreturn = ""
        self.subComA = Command(command="a", doc="DOC A",msgtypes=GroupMsgInfo, func=self.funcA)
        self.subComBA = Command(command="ba", doc="DOC ba",msgtypes=GroupMsgInfo, func=self.funcB)
        self.subComB = Command(command="b", doc="DOC B",msgtypes=GroupMsgInfo, sub=self.subComBA)
        self.subComC = Command(command="c", doc="DOC C",msgtypes=PrivateMsgInfo, sub=self.subComBA)
        self.root = Command(command="root", doc="DOC ROOT",msgtypes=None,
                            sub=[self.subComA, self.subComB,self.subComC])
        self.receiveEvent = ReceiveEvent(
            Eventer("test", ServiceType.Core), MsgEvent(msgInfo=GroupMsgInfo(1),msgContent=TextMsg("test")))

    def funcA(self,event):
        self.callreturn = "A"

    def funcB(self, event, s, a1="no"):
        self.callreturn = "B@%s@%s" % (s, a1)

    def funcC(self, event, s, *args):
        self.callreturn = "C@%s@%s" % (s, ''.join(args))

    def funcNo(self, event, s, *args, d):
        pass

    def funcYes(self, event, s, *args, d=None):
        pass

    def test_命令解析(self):
        test = Command._commandAnalysis("A B 'C D'")
        self.assertEqual(test, ["A", "B", "C D"])

        test = Command._commandAnalysis(""""A B"c D""")
        self.assertEqual(test, ["A Bc", "D"])

    def test_方法解析(self):
        a = FuncAttr(self.funcA)
        a.call(self.receiveEvent, [])
        self.assertEqual(self.callreturn, "A")

        b = FuncAttr(self.funcB)
        b.call(self.receiveEvent, ["a"])
        self.assertEqual(self.callreturn, "B@a@no")
        b.call(self.receiveEvent, ["a", 'b'])
        self.assertEqual(self.callreturn, "B@a@b")

        c = FuncAttr(self.funcC)
        with self.assertRaises(ArgsDifferentLengthCommandException):
            c.call(self.receiveEvent, [])  # 参数不匹配
        c.call(self.receiveEvent, ['a'])
        self.assertEqual(self.callreturn, "C@a@")
        c.call(self.receiveEvent, ['a', 'b', 'c', 'd'])
        self.assertEqual(self.callreturn, "C@a@bcd")

        with self.assertRaises(UnSupportArgsTypeException):
            FuncAttr(self.funcNo)  # 包含命名参数

    def test_命令测试(self):
        test = self.root.matchAndCall("root a", self.receiveEvent)
        self.assertEqual(test, True)
        self.assertEqual(self.callreturn, "A")

        test = self.root.matchAndCall("root b ba a", self.receiveEvent)
        self.assertEqual(test, True)
        self.assertEqual(self.callreturn, "B@a@no")

        test = self.root.matchAndCall("root b ba a '空 格'", self.receiveEvent)
        self.assertEqual(test, True)
        self.assertEqual(self.callreturn, "B@a@空 格")

    def test_调用空命令(self):
        try:
            self.root.matchAndCall("root b c", self.receiveEvent)
        except MatchAndCallException as e:
            self.assertEqual(e.type, MatchFailedCommandException)
            self.assertEqual(e.trace[0], self.subComB)

    def test_参数不匹配(self):
        try:
            self.root.matchAndCall("root a ba a b c", self.receiveEvent)
        except MatchAndCallException as e:
            self.assertEqual(e.type, ArgsDifferentLengthCommandException)
            self.assertEqual(e.trace[0], self.subComA)
    
    def test_消息类别错误(self):
        try:
            self.root.matchAndCall("root c", self.receiveEvent)
        except MatchAndCallException as e:
            self.assertEqual(e.type, MatchFailedCommandException)
