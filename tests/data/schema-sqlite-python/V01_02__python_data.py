def migrate(connection):
    cursor = connection.cursor()
    cursor.execute("CREATE TABLE python_test (id INTEGER PRIMARY KEY, data TEXT)")
    cursor.execute("INSERT INTO python_test (data) VALUES ('from_python')")
    cursor.execute("INSERT INTO pytest_base (name) VALUES ('inserted_by_python')")
