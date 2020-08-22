#
def tz_UTC(tz:int):
    """
    设定时区
    :param tz: 与 UTC 时区的时差
    """
    if tz <= -12 or tz >= 12:
        raise Exception()
    from datetime import timezone, timedelta
    return timezone(timedelta(hours=tz))
