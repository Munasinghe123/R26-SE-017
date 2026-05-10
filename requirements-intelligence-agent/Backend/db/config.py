

import pymysql

def get_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="sql123456!",
        database="requirements_extraction",
        cursorclass=pymysql.cursors.DictCursor
    )