class ApplicationError(Exception):
    """ Базовая ошибка приложения """


class UnknownPlatformError(ApplicationError):
    """ Ошибка при запросе несуществующей целевой платформы """


class DefinitionError(ApplicationError):
    """ Ошибка при парсинге схемы таблицы """

