from enum import Enum, unique
from .exception import APIError, BossIDError, NotLogin
from .ret import BossInfo, Damage, DamageList, TeamInfo, UserInfo
from typing import *
import httpx
from http.cookiejar import Cookie
import asyncio
import re


@unique
class BigFunAPILoginStatus(Enum):
    LOGGED = "LOGGED"  # 已登录
    SUCCCESS = "SUCCCESS"  # 登陆成功
    FAILER = "FAILER"  # 登录失败
    WAITSCAN = "WAITSCAN"  # 等待扫描
    SCANED = "SCANED"  # 已扫码
    NOT_CALL_LOGIN = "NOT_CALL_LOGIN"  # 没有挂起的登录操作


class BigFunAPI():
    def __init__(self, cookie: Optional[Dict[str, str]] = None) -> None:
        self._cookie = httpx.Cookies()
        self.__initCookie(cookie)
        self._ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36 Edg/85.0.564.51"
        self._api = "https://www.bigfun.cn/api/feweb"
        self._oauthKey: Optional[str] = None
        self._csrf = ""
        self._battleList = []
        self._bossList = []
        

    def cookie2Dict(self, source: httpx.Cookies = None):
        if source == None:
            source = self._cookie
        return self.__Cookie2DictHelper(source.jar._cookies)

    def __Cookie2DictHelper(self, list):
        l = {}
        for k, v in list.items():
            if isinstance(v, Cookie):
                l[k] = v.value
            else:
                l.update(self.__Cookie2DictHelper(v))
        return l

    def __initCookie(self, d: Optional[Dict[str, str]] = None):
        if d != None:
            for i, v in d.items():
                self._cookie.set(i, v, domain='.bigfun.cn')
        else:
            return

    def login(self):
        """
        BILIBILI OAuth 二维码登录
        :return : 登录url，需要转换为二维码
        """
        self._csrf = self._csrfToken()
        resp = self._req("GET", "https://passport.bigfun.cn/qrcode/getLoginUrl", headers={
            "origin": "https://www.bigfun.cn",
            "referer": "https://www.bigfun.cn/tools/pcrteam/boss",
            'user-agent': self._ua,
            'x-csrf-token': self._csrf
        }, cookiesync=True)
        if resp['code'] != 0:
            raise APIError(resp)
        self._oauthKey = resp['data']['oauthKey']
        return resp['data']['url']

    def checklogin(self):
        """
        判断登录二维码状态，若登录会自动执行登录操作，登录成功后建议保存 coocie 以便下次登录
        :return:
        """
        if self._oauthKey == None:
            return BigFunAPILoginStatus.NOT_CALL_LOGIN
        resp = self._req("POST", "https://passport.bigfun.cn/qrcode/getLoginInfo", data={
            "oauthKey": self._oauthKey
        }, headers={
            "origin": "https://www.bigfun.cn",
            "referer": "https://www.bigfun.cn/tools/pcrteam/boss",
            'user-agent': self._ua,
            'x-csrf-token': self._csrf
        }, cookiesync=True)
        if resp['status']:
            self._oauthKey = None
            if self._cookie.get('SESSDATA', None) == None:
                return BigFunAPILoginStatus.FAILER
            self._oauthKey == None
            self._oauthBilibili()
            resp = self._req("POST", "https://www.bigfun.cn/api/feweb?target=login/a", data={}, headers={
                "origin": "https://www.bigfun.cn",
                "referer": "https://www.bigfun.cn/tools/pcrteam/boss",
                'user-agent': self._ua,
                'x-csrf-token': self._csrf
            }, cookiesync=True)
            if 'errors' in resp.keys():
                return BigFunAPILoginStatus.FAILER
            return BigFunAPILoginStatus.SUCCCESS
        else:
            if resp['data'] == -2:
                self._oauthKey = None
                return BigFunAPILoginStatus.LOGGED
            elif resp['data'] == -4:
                return BigFunAPILoginStatus.WAITSCAN
            elif resp['data'] == -5:
                return BigFunAPILoginStatus.SCANED
            else:
                raise APIError(resp)

    def _oauthBilibili(self):
        resp = self._req("GET", "https://passport.bigfun.cn/web/sso/list", params={'biliCSRF': self._cookie['bili_jct']}, data={}, headers={
            "origin": "https://www.bigfun.cn",
            "referer": "https://www.bigfun.cn/tools/pcrteam/boss",
            'user-agent': self._ua
        }, cookiesync=True)
        for url in resp['data']['sso']:
            resp = self._req("POST", url, data={}, headers={
                "origin": "https://www.bigfun.cn",
                "referer": "https://www.bigfun.cn/tools/pcrteam/boss",
                'user-agent': self._ua
            }, cookiesync=True)

    _RE_CSRF = re.compile(r'<meta name="csrf-token" content="(.*?)"/>')

    def _csrfToken(self):
        resp = httpx.get("https://www.bigfun.cn/tools/pcrteam/boss", headers={
            "origin": "https://www.bigfun.cn",
            'user-agent': self._ua
        }, cookies=self._cookie)
        self.__initCookie(self.cookie2Dict(resp.cookies))
        return self._RE_CSRF.findall(resp.text)[0]

    @property
    def islogin(self):
        """
        判断登录状态
        """
        try:
            self._reqapi({
                'target': "gzlj-auth-state/a"
            })
        except APIError as e:
            if e.msg['code'] == 401:
                return False
            else:
                raise e
        self._islogin = True
        return True

    def _req(self, method, api, params=None, headers=None, data=None, cookiesync=False):
        r = httpx.request(method, api, params=params, headers=headers,
                          cookies=self._cookie, data=data)
        if cookiesync:
            self.__initCookie(self.cookie2Dict(r.cookies))
        resp: Dict[Any, Any] = r.json()
        if resp.get('code', 0) == 401:
            raise NotLogin(resp)
        if resp.get('code', 0) != 0:
            raise APIError(resp)
        return resp

    def _reqapi(self, params=dict()):
        return self._req("GET", self._api, params, {'Accept': '*/*',
                                                    'Accept-Encoding': 'gzip, deflate',
                                                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
                                                    'Connection': 'keep-alive',
                                                    'Host': 'www.bigfun.cn',
                                                    "origin": "https://www.bigfun.cn",
                                                    "referer": "https://www.bigfun.cn/tools/pcrteam/boss",
                                                    'Sec-Fetch-Dest': 'empty',
                                                    'Sec-Fetch-Mode': 'cors',
                                                    'Sec-Fetch-Site': 'none',
                                                    'user-agent': self._ua})

    def userInfo(self):
        """获得 API 登录用户的用户信息"""
        resp = self._reqapi({
            'target': 'get-gzlj-user-info/a',
            'flush_user_info': 0
        })
        return UserInfo(resp['data'])

    def playerIDandPlayerName(self):
        """获得玩家 id 和玩家名的映射"""
        resp = self._reqapi({
            'target': 'gzlj-clan-collect-report/a'
        })
        playerMapping: Dict[int, str] = {}
        for row in resp['data']['data']:
            playerMapping[row['viewer_id']] = row['username']
        return playerMapping

    def battleIDList(self):
        """
        获得公会战历史列表及id
        :return: 列表 [{'id':int,'name':str}]
        """
        resp = self._reqapi({
            'target': "gzlj-clan-battle-list/a"
        })
        self._battleList = resp['data']
        return resp['data']

    def bossList(self, battleID):
        """
        获取指定公会战的boss id
        :return: 字典 {id:boss_name}
        """
        resp = self._reqapi({
            'target': "gzlj-clan-boss-report-collect/a",
            'battle_id': battleID
        })
        self._bossList:List[BossInfo] =  []
        for boss in resp['data']['boss_list']:
            self._bossList.append(BossInfo(boss))
        return self._bossList

    def damageList(self, battleID, bossID, page):
        """
        获得伤害列表
        """
        for boss in self._bossList:
            if bossID ==boss.id:
                break
        else:
            raise BossIDError
        resp = self._reqapi({
            'target': "gzlj-clan-boss-report/a",
            'battle_id': battleID,
            'boss_id': bossID,
            'page': page
        })
        if len(resp['data']) == 0:
            return False
        else:
            return DamageList(resp['data'])

    def allDamageList(self, battleID, bossid):
        """获得伤害列表,生成器类型"""
        p = 1
        while True:
            page = self.damageList(battleID, bossid, p)
            if page == False:
                break
            p += 1
            if page:
                for row in page:
                    row: Damage
                    yield row
                if len(page) < 25:
                    break
            else:
                break
    def rank(self):
        """
        获得排名信息
        """
        resp = self._reqapi({
            'target': "gzlj-my-clan/a"
        })
        if resp['code'] != 0:
            return False
        else:
            return TeamInfo(resp['data'])