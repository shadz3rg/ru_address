
class ApplicationError(Exception):
    pass


class UnknownPlatformError(ApplicationError):
    pass


class DefinitionError(ApplicationError):
    pass
