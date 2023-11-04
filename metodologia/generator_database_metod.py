import sqlite3

conexion = sqlite3.connect("metodologia_rfid.db")
conexion.execute("""create table if not exists RFID (
                          ID integer primary key AUTOINCREMENT,
                          hexcode text,
                          letter text
                    )""")
conexion.close()
