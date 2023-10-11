class Constants:
    table_columns_default = [
        "query",
        "rows",
        "calls",
        "total_exec_time",
        "shared_blks_read",
        "shared_blks_written",
        "local_blks_read",
        "local_blks_written",
        "query_start",
        "backend_start"
    ]
    table_columns_ins_upt_del = [
        "имя таблицы",
        "кол. вставленных строк",
        "кол. обновленных строк",
        "кол. удаленных строк",
        "кол. последовательных сканирований (seq_scan)",
        "кол. сканирований индекса (inx_scan)",
        "кол. мертвых (неактивных) строк",
        "", "", ""]

    top_20_query = [
        "запрос",
        "общее время выполнения",
        "кол. вызовов",
        "среднее время выполнения",
        "Доля времени выполнения CPU",
        "", "", "", "", ""]


def list_include() -> object:
    return [
        ("themes", "themes"),
        ("icons", "icons"),
        ("version.txt", "version.txt"),
        ("auth.json", "auth.json")
    ]


def table_columns_default():
    return Constants.table_columns_default


def table_columns_ins_upt_del():
    return Constants.table_columns_ins_upt_del


def top_20_query():
    return Constants.top_20_query


def pg_stat_user_tables_query():
    """
    Запрос для получения количества удалённых, обновлённых и изменённых записей в таблицах.

    :return: None
    """

    query_template = """SELECT relname, 			-- имя таблицы.                               
                               n_tup_ins,			-- количество вставленных строк в таблицу
                               n_tup_upd,			-- количество обновленных строк в таблице
                               n_tup_del,			-- количество удаленных строк из таблицы
                               seq_scan,			-- количество последовательных сканирований (sequential scans) таблицы
                               idx_scan,			-- количество индексных сканирований таблицы
                               n_dead_tup			-- текущее количество мертвых (удаленных) строк в таблице
                          FROM pg_stat_user_tables
                         WHERE relname IN ({})
                         ORDER BY n_tup_ins DESC;"""
    return query_template


def get_search_query(dbname_str, like_str):
    """
    Запрос для поиска по базе данных.
    :param dbname_str: Имя базы данных
    :param like_str: Строка для поиска
    :return: SQL-запрос
    """

    if like_str.startswith('pa_'):
        like_str = like_str[3:]
        search_condition = f"pa.query LIKE '%{like_str}%'"
    elif like_str.startswith('all_'):
        like_str = like_str[4:]
        search_condition = f"pg.query LIKE '%{like_str}%' OR pa.query LIKE '%{like_str}%'"
    else:
        # Если нет префикса, ищем как по pg, так и по pa
        search_condition = f"pg.query LIKE '%{like_str}%'"

    # Создаем запрос, включая строку поиска
    query = f"""SELECT DISTINCT
                    pg.query AS pg_query_text, 							-- Текст выполненного SQL-запроса.
                    pg.rows AS affected_rows,							-- Количество строк, затронутых запросом.
                    pg.calls AS query_calls, 							-- Количество вызовов данного запроса.                   
                    pg.total_exec_time AS total_execution_time, 		-- Общее время выполнения запроса.
                    pg.shared_blks_read AS shared_blocks_read, 			-- Количество чтений блоков.
                    pg.shared_blks_written AS shared_blocks_written, 	-- Количество записанных блоков.
                    pg.local_blks_read AS local_blocks_read, 			-- Количество чтений локальных блоков.
                    pg.local_blks_written AS local_blocks_written, 		-- Количество записанных локальных блоков.
                    pa.query_start AS query_start_time, 				-- Время начала выполнения запроса.
                    pa.backend_start AS backend_start_time 			    -- Время старта бэкенд-процесса, выполнившего запрос.
                FROM pg_stat_statements pg
                JOIN pg_database db ON pg.dbid = db.oid
                JOIN pg_authid auth ON pg.userid = auth.oid
                JOIN pg_stat_activity pa ON db.oid = pa.datid AND auth.oid = pa.usesysid
                WHERE db.datname = '{dbname_str}' AND ({search_condition})
                ORDER BY pa.query_start DESC;"""
    return query


def get_execute_query(dbname_str):
    """
    Запрос к базе данных.
    :param dbname_str: Имя базы данных
    :return: SQL-запрос
    """
    query = f"""SELECT DISTINCT
                    pg.query AS pg_query_text, 							-- Текст выполненного SQL-запроса.
                    pg.rows AS affected_rows,							-- Количество строк, затронутых запросом.
                    pg.calls AS query_calls, 							-- Количество вызовов данного запроса.                   
                    pg.total_exec_time AS total_execution_time, 		-- Общее время выполнения запроса.
                    pg.shared_blks_read AS shared_blocks_read, 			-- Количество считанных разделяемых блоков.
                    pg.shared_blks_written AS shared_blocks_written, 	-- Количество записанных разделяемых блоков.
                    pg.local_blks_read AS local_blocks_read, 			-- Количество считанных локальных блоков.
                    pg.local_blks_written AS local_blocks_written, 		-- Количество записанных локальных блоков.
                    pa.query_start AS query_start_time, 				-- Время начала выполнения запроса.
                    pa.backend_start AS backend_start_time  			-- Время старта бэкенд-процесса, выполнившего запрос.
                FROM pg_stat_statements pg
                JOIN pg_database db ON pg.dbid = db.oid
                JOIN pg_authid auth ON pg.userid = auth.oid
                JOIN pg_stat_activity pa ON db.oid = pa.datid AND auth.oid = pa.usesysid
                WHERE db.datname = '{dbname_str}'
                ORDER BY pa.query_start DESC;"""
    return query


def get_20_top_query(dbname_str):
    """
    Запрос для получения топ-20 самых тяжелых запросов.
    :param dbname_str: Имя базы данных
    :return: SQL-запрос
    """

    query = f"""SELECT query                                                         AS query,
                       round(pg.total_exec_time::numeric, 2)                         AS total_time,
                       calls,
                       round(pg.mean_exec_time::numeric, 2)                          AS mean,
                       round((100 * pg.total_exec_time /
                              sum(pg.total_exec_time::numeric) OVER ())::numeric, 2) AS percentage_cpu
                  FROM pg_stat_statements pg
                           JOIN pg_database db ON pg.dbid = db.oid
                 WHERE db.datname = '{dbname_str}'
                 ORDER BY total_time DESC
                 LIMIT 20;"""
    return query
