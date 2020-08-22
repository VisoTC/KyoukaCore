
from Core.Interface.IPlugin import IPlugin
from Core.Interface.Msg.MsgBase import MsgEvent
from Core.Interface.Msg.MsgContent import TextMsg

import requests

class Setu(IPlugin):
    
    def GroupMsg(self,msg:MsgEvent):
        if len(msg.msgContent) != 0:
            a = msg.msgContent[0]
            if isinstance(a,TextMsg):
                if a.content.find("/hso") == 0:
                    self.hso(msg)
    
    def hso(self,msg):
        apikey = self.config.get('apikey',"")
        if len(apikey) == 0:
            
        r = requests.get('https://api.lolicon.app/setu/',params={
            'apikey':apikey
        })# TODO 等我有空再写
