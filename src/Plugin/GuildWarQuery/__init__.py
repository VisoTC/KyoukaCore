import json
from Core.Interface.IPlugin import IPlugin
from Core.Interface.Msg.MsgBase import MsgEvent
from Core.Interface.Msg.MsgContent import TextMsg, PicMsg
import time
import requests

from Core.Interface.Msg.MsgInfo import GroupMsgInfo


class GuildWarQuery(IPlugin):

    @staticmethod
    def PluginInfo():
        '''
        插件信息
        :return Config
        '''
        return {
            "packageName": "com.visotc.KyoukaCore.GuildWarQuery",  # 包名，唯一标识
            "name": "GuildWarQuery",  # 显示名称
            "version": "v1.dev",  # 版本号
            "author": "Viso-TC",  # 作者
            "entrance": GuildWarQuery  # 入口类
        }

    @property
    def pluginInfo(self):
        return self.PluginInfo()

    api = 'https://service-kjcbcnmw-1254119946.gz.apigw.tencentcs.com'

    def fromGroupMsgInfo(self, msg):
        # 只接受文本消息
        if len(msg.msgContent) != 1 and not isinstance(msg.msgContent[0], TextMsg):
            return
        else:
            if isinstance(msg.msgContent[0], TextMsg):
                testMsg = msg.msgContent[0]
            else:
                return
        if testMsg.content[:9].lower() == "/pcr rank":
            if len(testMsg.content) > 10:
                if not testMsg.content[9] == " ":
                    self._reply(msg, TextMsg("PCR 公会战排名查询插件：指令之间需要输入空格哦"))
                    return
                else:
                    if not testMsg.content[10:].isdigit():
                        self._reply(msg, TextMsg("PCR 公会战排名查询插件：需要输入数字哦"))
                        return
                    else:
                        history = int(testMsg.content[10:])
            else:
                history = 0
            self._reply(msg, self.rank(history))
        elif testMsg.content == "/pcr history":
            self._reply(msg, self.history())
        elif testMsg.content[0:4].lower() == "/pcr":
            self._reply(msg, TextMsg(
                "公会战排名查询插件：\n" +
                "/pcr Rank <[可选]历史存档时间戳>：查看公会战排名情况\n" +
                "/pcr History：查看历史存档时间戳\n"))

    def rank(self, history=0):
        """
        查询公会战成绩
        API来源: https://kengxxiao.github.io/Kyouka/
        :param history: 历史记录时间戳
        """
        leaderName = "虚度年华"
        r = requests.post(self.api + '/leader/0',
                          json={"history": history,
                                "leaderName": "虚度年华"},
                          headers={
                              'Custom-Source': "VisoTC/KyoukaCore",
                              'Referer': 'https://kengxxiao.github.io/Kyouka/',
                              'Origin': 'https://kengxxiao.github.io'})

        if r.status_code != 200:
            return TextMsg("访问 API 时发生错误,HTTP:%s" % r.status_code)
        resp = r.json()
        if resp['code'] != 0:
            return TextMsg("API 错误代码{}：{}".format(resp['code'], resp['msg']))
        timeStr = time.strftime("%Y年%m月%d %H:%M:%S",
                                time.localtime(resp['ts']))
        if len(resp['data']) == 0:
            return TextMsg("在时间点：{}找不到会长名为：{} 的公会".format(timeStr, leaderName))
        msgLink = []
        TextTemplate = "工会：{name}（会长：{leader_name}）排名：{rank}"
        for row in resp['data']:
            msgLink.append(TextTemplate.format(
                name=row['clan_name'], leader_name=row['leader_name'], rank=row['rank']))
        msgLink.append("数据统计时间：{}\n".format(timeStr))
        return TextMsg("\n".join(msgLink))

    def history(self):
        """
        查询存档公会战成绩时间戳
        API来源: https://kengxxiao.github.io/Kyouka/
        :param history: 历史记录时间戳
        """
        r = requests.get(self.api + '/default',
                         headers={
                             'Custom-Source': "VisoTC/KyoukaCore",
                             'Referer': 'https://kengxxiao.github.io/Kyouka/',
                             'Origin': 'https://kengxxiao.github.io'})
        if r.status_code != 200:
            return TextMsg("访问 API 时发生错误")
        resp = r.json()
        if resp['code'] != 0:
            return TextMsg("API 错误代码{}：{}".format(resp['code'], resp['msg']))
        if len(resp.get('historyV2', {}).keys()) == 0:
            return TextMsg("PCR 公会战排名查询插件：历史时间戳为空")
        textMsg = ["时间戳-存档内容"]
        for history in resp.get('historyV2', {}).keys():
            if resp.get('historyV2')[history] == "":
                text = time.strftime("%Y年%m月%d %H:%M:%S",
                                     time.localtime(int(history)))
            else:
                text = resp.get('historyV2')[history]
            textMsg.append("{}-{}".format(history, text))
        return TextMsg("\n".join(textMsg))

    def run(self):
        self.callback(self.fromGroupMsgInfo, GroupMsgInfo)
        self.loadDone()


pluginInfo = GuildWarQuery.PluginInfo()
