async def migrate(connection):
    cursor = connection.cursor()
    cursor.execute("CREATE TABLE async_python_test (id INTEGER PRIMARY KEY, data TEXT)")
    cursor.execute("INSERT INTO async_python_test (data) VALUES ('from_async_python')")
