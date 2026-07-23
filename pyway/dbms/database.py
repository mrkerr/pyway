from pydoc import locate
from typing import Any, Union

VALID_DATABASE_TYPES = ('postgres', 'mysql', 'sqlite', 'duckdb')


def factory(dbms: Union[str, None]) -> Any:
    dbms_class = locate('pyway.dbms.%s.%s' % (dbms, dbms.title())) if dbms else None
    if dbms_class is None:
        raise ValueError(f"Unsupported database type '{dbms}', valid types: {', '.join(VALID_DATABASE_TYPES)}")
    return dbms_class
