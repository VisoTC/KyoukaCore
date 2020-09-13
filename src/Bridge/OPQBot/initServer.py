from Core.Service.Bridge import BridgeService, ServiceInfo

service = BridgeService(ServiceInfo(**{
    'packageName': "com.visotc.KyoukaCore.Bridge.OPQBot",
    'name': "OPQBot 机器人桥",
    'version': "dev.2",
    'author': "VisoTC"
}))

if service.config.isEmpty:
    service.config.data = {
        "qq": "在此输入qq号",
        "webapi": "http://127.0.0.1:8888"
    }
    service.config.commit()