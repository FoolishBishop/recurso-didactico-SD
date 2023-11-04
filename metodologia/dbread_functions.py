import sqlite3


def load_values(connection, table, column_names_tuple, values_tuple):
    cursor = connection.cursor()
    insert_w_param = f"""INSERT INTO {table}
                      ({", ".join(column_names_tuple)}) 
                      VALUES ({("?," * len(values_tuple))[:-1]})"""
    cursor.execute(insert_w_param, values_tuple)
    connection.commit()
    connection.close()


def read_values_hexcode(hexcode_code):
    conn = sqlite3.connect("metodologia_rfid.db")
    cursor = conn.cursor()
    consulta = f"SELECT letter " \
               f"FROM RFID " \
               f"WHERE hexcode = ?"
    cursor.execute(consulta, (hexcode_code,))
    tupppple = cursor.fetchone()
    return tupppple[0]


print(read_values_hexcode("j"))
