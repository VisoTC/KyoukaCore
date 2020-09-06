from ...exception import KyoukaException

class MsgEventException(KyoukaException):...

class MsgContentTypeUnsupported(MsgEventException):...


class PicMsgEventException(MsgEventException):...
class DownloadFailPicException(PicMsgEventException):...
class UnknowPicTypeException(PicMsgEventException):...