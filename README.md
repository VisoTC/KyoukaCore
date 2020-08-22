# KyoukaCore
> 一个通用的机器人平台，目的是创建平台无关的机器人平台
> 
> 正在开发中，目前兼容 Bot 框架为 [OPQBOT](https://github.com/OPQBOT/OPQ)
>
> 当前唯一指定插件为：PCR 报刀插件（开发中）

当前处于开发状态，随时会有更变
## 架构
基于事件的架构，使用协程处理事件循环，各插件运行在不同线程上

[Bridge] <==> [KyoukaCore] <==> [Plugin]
### Bridge
连接到各个不同的机器人平台

具体实现由 KyoukaCore 抽象的各类方法与事件
### KyoukoCore
抽象各类接口并将各类 API 提供给 Plugin
### Plugin
实现各种功能的插件

## 如何安装并启动
Python 3.7+(使用了 async/await)

```
git clone <this git url>
```

