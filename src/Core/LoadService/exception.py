from ..exception import KyoukaException

class LoadServiceBaseException(KyoukaException):
    '''LoadService 基础错误类'''

class NotDirException(LoadServiceBaseException):
    """载入的路径不是文件夹"""