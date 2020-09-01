from . import EventPayloadBase

class TestEvent(EventPayloadBase):
    def __str__(self) -> str:
        return "this test msg"
    
    def __repr__(self) -> str:
        return "TestEvent()" 