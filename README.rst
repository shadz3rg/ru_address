Конвертация БД ГАР (ex. ФИАС/КЛАДР) в SQL/CSV/TSV дамп
==========================================

| Утилита для командной строки, позволяющая сконвертировать схему, данные и ключи ГАР для импорта в БД MySQL/PostgreSQL/ClickHouse.
Благодаря SAX парсеру потребляет небольшое количество ресурсов (не более 50 мб памяти).

Для начала необходимо скачать актуальную XSD схему и последнюю XML выгрузку с данными ГАР, распаковать их в одну из директорий и запустить команду.

Все нужные файлы можно скачать с сайта-источника ФНС России https://fias.nalog.ru/Frontend

Установка
---------
Требуется Python 3.6+
::

    $ git clone https://github.com/shadz3rg/ru_address.git && cd ru_address && python setup.py install

Использование
-------------

Установка пакета дает доступ к исполняемому файлу ``ru_address``.

Конвертация схемы:
^^^^^^^^^^^^^^^^^^
::

    $ ru_address schema --help
    Usage: ru_address schema [OPTIONS] SOURCE_PATH OUTPUT_PATH

      Convert XSD schema into target platform definitions. 
      Get latest schema @ https://fias.nalog.ru/docs/gar_schemas.zip
    
    Options:
      --target [mysql|psql|ch]  Target DB
      --table TEXT              Limit table list to process
      --no-keys                 Exclude keys && column index
      --encoding TEXT           Default table encoding
      --help                    Show this message and exit.
::

  # Простейший вариант
  $ ru_address /путь/к/файлам /путь/для/экспорта
  # С ограниченным списком таблиц
  $ ru_address /путь/к/файлам /путь/для/экспорта --table=ADDHOUSE_TYPES --table=HOUSE_TYPES
  # Экспорт всех таблиц в один файл
  $ ru_address /путь/к/файлам /путь/для/экспорта/schema.sql 

Конвертация данных:
^^^^^^^^^^^^^^^^^^^
::

    $ ru_address dump --help
    Usage: ru_address dump [OPTIONS] SOURCE_PATH OUTPUT_PATH SCHEMA_PATH

      Convert tables content into target platform dump file.

    Options:
      --target [sql|csv|tsv]  Target dump format
      --region TEXT           Limit region list to process
      --table TEXT            Limit table list to process
      --help                  Show this message and exit.
::

  # Простейший вариант
  $ ru_address /путь/к/файлам /путь/для/сохранения /путь/к/xsd-схеме
  # С ограниченным списком таблиц
  $ ru_address /путь/к/файлам /путь/для/сохранения /путь/к/xsd-схеме --table=ADDHOUSE_TYPES --table=HOUSE_TYPES
  # С ограниченным списком регионов
  $ ru_address /путь/к/файлам /путь/для/сохранения /путь/к/xsd-схеме --region=01 --region=02
