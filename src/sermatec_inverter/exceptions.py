class ResponseMalformed(Exception):
    pass

class NoDataReceived(Exception):
    pass

class FailedResponseIntegrityCheck(Exception):
    pass

class NotConnected(Exception):
    pass

class ProtocolFileMalformed(Exception):
    pass

class CommandNotFoundInProtocol(Exception):
    pass

class ParsingNotImplemented(Exception):
    pass