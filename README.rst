ru_address: Конвертация БД ФИАС в SQL дамп
==========================================

Утилита для коммандной строки, позволяющая скновертировать схему, данные и ключи БД ФИАС для импорта в SQL базу.
Все нужные файлы можно скачать с сайта-источника ФНС России https://fias.nalog.ru/Updates.aspx
Требуется установленный Python 3.6

Установка
---------

Простой способ:

::

    $ pip install ru_address


Чуть более сложный способ:

::

    $ git clone https://github.com/shadz3rg/ru_address.git && cd ru_address && python setup.py install

Использование
-------------

Установка пакета дает доступ к CLI исполняемому файлу ``ru_address``.

::

    $ ru_address --help
    Usage: ru_address [OPTIONS] SOURCE_PATH OUTPUT_PATH

      Подготавливает БД ФИАС для использования с SQL. XSD файлы и XML выгрузку
      можно получить на сайте ФНС https://fias.nalog.ru/Updates.aspx

    Options:
      --join TEXT         Join dump into single file with given filename
                          Опция позволяет объединить весь дамп в один файл (по умолчанию отдельный файл для каждой таблицы)
      --source [xml|dbf]  Data source file format
                          Формат источника данных, dbf пока не реализован
      --table-list TEXT   Comma-separated string for limiting table list to process
                          Список таблиц для обработки, указывается строкой с разделением запятой
      --no-data           Skip table definition in resulting file
                          Пропустить вставку данных
      --no-definition     Skip table data in resulting file
                          Пропустить создание схемы
      --encoding TEXT     Default table encoding
                          Кодировка для таблицы, по умолчанию utf8mb4
      --version           Show the version and exit.
      --help              Show this message and exit.

Для начала необходимо скачать XSD схему с XML данными ФИАС и распаковать их в одну папку.
Простейший вариант полная конвертация:

::

  $ ru_address /путь/к/файлам /путь/для/сохранения --join=dump.sql

Только необходимые таблицы:

::

  $ ru_address /путь/к/файлам /путь/для/сохранения --table-list=ACTSTAT,ADDROBJ
