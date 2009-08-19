class BaseCloneError(Exception):
    # don't use directly
    def __init__(self, value = None):
        if value is not None:
            self.parameter = value
    def __str__(self):
        return repr(self.parameter)
    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, repr(self.parameter))

class CloneError(BaseCloneError):
    # logic error?
    pass
class CloneNotFoundError(BaseCloneError):
    # http not found
    pass
class CloneIOError(BaseCloneError):
    # socket et al
    pass

