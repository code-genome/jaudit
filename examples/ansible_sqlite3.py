
import json
import sys
import sqlite3
import os
import time

class SQLiteLogger:

    def __init__(self, **args):
        dbname = args['dbname']
        self.__table = args['table']

        self.__db = sqlite3.connect(dbname)
        self.__db.execute(f"CREATE TABLE IF NOT EXISTS {self.__table} (host, timestamp, status, scan_result, error, UNIQUE(host))")
        self.__db.commit()

    def log(self, record):
        now = time.gmtime()
        y = now.tm_year
        m = now.tm_mon
        d = now.tm_mday
        h = now.tm_hour
        mn = now.tm_min

        ts = f"{y}/{m:02d}/{d:02d} {h:02d}:{mn:02d}"
        host=record['inventory_name']
        status = record['status']
        scan_result = None
        error=None
        
        if record['status'] == 'ok':
            scan_result = json.dumps(record)
        elif record['status'] == 'failed':
            error = record['error']
        elif record['status'] == 'down':
            error = record['error']

        self.__db.execute(f"REPLACE INTO {self.__table} VALUES (?, ?, ?, ?, ?)",
                          (host, ts, status, scan_result, error))

        self.__db.commit()
