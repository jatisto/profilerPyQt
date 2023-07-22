class Constants:
    table_columns_default = ["QUERY", "ROWS", "CALLS", "QUERY_START", "BACKEND_START"]
    table_columns_ins_upt_del = ["RELNAME", "N_TUP_INS", "N_TUP_UPD", "N_TUP_DEL", "N_DEAD_TUP"]


def table_columns_default():
    return Constants.table_columns_default


def table_columns_ins_upt_del():
    return Constants.table_columns_ins_upt_del


def pg_stat_user_tables_query():
    query_template = "SELECT " \
                     "relname, " \
                     "n_tup_ins, " \
                     "n_tup_upd, " \
                     "n_tup_del, " \
                     "n_dead_tup " \
                     "FROM pg_stat_user_tables " \
                     "WHERE relname IN ({}) " \
                     "ORDER BY n_tup_ins DESC;"
    return query_template


def get_search_query(dbname_str, like_str):
    query = "SELECT DISTINCT\n" \
            "    pg.query,\n" \
            "    pg.rows,\n" \
            "    pg.calls,\n" \
            "    pa.query_start,\n" \
            "    pa.backend_start\n" \
            "FROM pg_stat_statements pg\n" \
            "    JOIN pg_database db ON pg.dbid = db.oid\n" \
            "    JOIN pg_authid auth ON pg.userid = auth.oid\n" \
            "    JOIN pg_stat_activity pa ON db.oid = pa.datid AND auth.oid = pa.usesysid\n" \
            f"WHERE db.datname = '{dbname_str}'\n" \
            f"AND pg.query LIKE '%{like_str}%'\n" \
            "ORDER BY pa.query_start DESC;"
    return query


def get_execute_query(dbname_str):
    query = "SELECT DISTINCT\n" \
            "    pg.query,\n" \
            "    pg.rows,\n" \
            "    pg.calls,\n" \
            "    pa.query_start,\n" \
            "    pa.backend_start\n" \
            "FROM pg_stat_statements pg\n" \
            "    JOIN pg_database db ON pg.dbid = db.oid\n" \
            "    JOIN pg_authid auth ON pg.userid = auth.oid\n" \
            "    JOIN pg_stat_activity pa ON db.oid = pa.datid AND auth.oid = pa.usesysid\n" \
            f"WHERE db.datname = '{dbname_str}'\n" \
            "ORDER BY pa.query_start DESC;"
    return query
