ru_address: обработка БД ГАР (ex. ФИАС/КЛАДР)
=============================================

| Утилита для конвертации схемы, ключей и данных выгрузки ГАР под импорт в БД **MySQL/PostgreSQL/ClickHouse**.
Благодаря SAX парсеру потребляет небольшое количество ресурсов (не более 50 мб памяти).

Установка
---------
Требуется Python 3.6+
::

    $ git clone https://github.com/shadz3rg/ru_address.git && cd ru_address 
    $ # deprecated python setup.py install
    $ ~/.local/bin/pip install .

Использование
-------------

| Для начала необходимо скачать актуальную **XSD** схему и **XML** выгрузку с данными ГАР, распаковать на диск.
Все нужные файлы публикуются на оф. сайте ФНС России https://fias.nalog.ru/Frontend

| Установка пакета дает доступ к исполняемому файлу ``ru_address`` и его под-командам:

Конвертация схемы:
^^^^^^^^^^^^^^^^^^

Поддерживаемые форматы схемы и их параметры
"""""""""""""""""""""""""""""""""""""""""""
.. list-table::
   :header-rows: 1

   * - Формат
     - ENV параметры
   * - MySQL (mysql)
     - | ``RA_INCLUDE_DROP`` - Добавить ``DROP IF EXIST`` (по умолчанию *"1"*)
       | ``RA_TABLE_ENGINE`` - Движок таблицы (по умолчанию *"MyISAM"*)
   * - PostgreSQL (psql)
     - | ``RA_INCLUDE_DROP`` - Добавить ``DROP IF EXIST`` (по умолчанию *"1"*)
   * - ClickHouse (ch)
     - | ``RA_INCLUDE_DROP`` - Добавить ``DROP IF EXIST`` (по умолчанию *"1"*)
       | ``RA_TABLE_ENGINE`` - Движок таблицы (по умолчанию *"MergeTree"*)

Описание
""""""""
::

    $ ru_address schema --help
    Usage: python -m ru_address.command schema [OPTIONS] SOURCE_PATH OUTPUT_PATH

    Convert XSD content into target platform schema definitions.
    Get latest schema at https://fias.nalog.ru/docs/gar_schemas.zip
    Generate file per table if `output_path` argument is existing directory;
    else dumps all tables into single file.

    Options:
      --target [mysql|psql|ch]  Target schema format
      -t, --table TEXT          Limit table list to process
      --no-keys                 Exclude keys && column index
      --help                    Show this message and exit.

Примеры
"""""""
.. code-block:: shell

  # Простейший вариант
  $ ru_address schema /путь/к/файлам /путь/для/экспорта
  # С ограниченным списком таблиц
  $ ru_address schema /путь/к/файлам /путь/для/экспорта --table=ADDHOUSE_TYPES --table=HOUSE_TYPES
  # Экспорт всех таблиц в один файл
  $ ru_address schema /путь/к/файлам /путь/для/экспорта/schema.sql

Конвертация данных:
^^^^^^^^^^^^^^^^^^^

Поддерживаемые форматы дампа и их параметры
"""""""""""""""""""""""""""""""""""""""""""
.. list-table::
   :header-rows: 1

   * - Формат
     - ENV параметры
   * - MySQL (mysql)
     - | ``RA_BATCH_SIZE`` - Разделить ``INSERT INTO`` на части по n-записей (по умолчанию *"500"*)
       | ``RA_SQL_ENCODING`` - Кодировка данных (по умолчанию *"utf8mb4"*)
   * - PostgreSQL (psql)
     - | ``RA_BATCH_SIZE`` - Разделить ``INSERT INTO`` на части по n-записей (по умолчанию *"500"*)
   * - CSV (csv)
     - —
   * - TSV (tsv)
     - —

Описание
"""""""
::

    $ ru_address dump --help
    Usage: python -m ru_address.command dump [OPTIONS] SOURCE_PATH OUTPUT_PATH [SCHEMA_PATH]

    Convert XML content into target platform dump files.
    Get latest data at https://fias.nalog.ru/Frontend

    Options:
      --target [mysql|psql|csv|tsv]   Target dump format
      -r, --region TEXT               Limit region list to process
      -t, --table TEXT                Limit table list to process
      -m, --mode [direct|per_region|per_table|region_tree]
                                      Dump output mode (only if `output_path` argument is a valid directory)
      --help                          Show this message and exit.

Примеры
"""""""
.. code-block:: shell

  # Простейший вариант
  $ ru_address dump /путь/к/файлам /путь/для/сохранения /путь/к/xsd-схеме
  # С указанием режима вывода:
  # - direct        Вывод в единый файл, используется по умолчанию если /путь/для/сохранения - файл
  # - per_region    Вывод данных в единый файл на каждый регион
  # - per_table     Вывод данных в единый файл на каждую таблицу
  # - region_tree   Вывод повторяет исходную структуру файлов (по умолчанию)
  $ ru_address dump /путь/к/файлам /путь/для/сохранения /путь/к/xsd-схеме --mode=per_table
  # С ограниченным списком таблиц
  $ ru_address dump /путь/к/файлам /путь/для/сохранения /путь/к/xsd-схеме --table=ADDHOUSE_TYPES --table=HOUSE_TYPES
  # С ограниченным списком регионов
  $ ru_address dump /путь/к/файлам /путь/для/сохранения /путь/к/xsd-схеме --region=01 --region=02
  # Экспорт всех таблиц в один файл
  $ ru_address dump /путь/к/файлам /путь/для/экспорта/dump.sql /путь/к/xsd-схеме

FAQ
---------
Как передать ENV параметры в приложение?
   .. code-block:: shell

      # Linux (стандартные ENV переменные, в т.ч. на уровне системы)
      $ RA_BATCH_SIZE=1000 RA_SQL_ENCODING=utf8 ru_address dump ...
      # Linux / Windows
      $ ru_address -e RA_BATCH_SIZE 1000 -e RA_SQL_ENCODING utf8 dump ...  
     
Как импортировать CSV данные?
  .. code-block:: shell

      # На примере MariaDB:
      $ MariaDB [ru_address]> LOAD DATA INFILE '/var/dump/ADDHOUSE_TYPES.csv' INTO TABLE ADDHOUSE_TYPES FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\r\n';

Как импортировать TSV данные?
  .. code-block:: shell

      # На примере MariaDB:
      $ MariaDB [ru_address]> LOAD DATA INFILE '/var/dump/ADDHOUSE_TYPES.tsv' INTO TABLE ADDHOUSE_TYPES LINES TERMINATED BY '\r\n';
