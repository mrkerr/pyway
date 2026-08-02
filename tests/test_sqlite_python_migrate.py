import os
import sqlite3
import pytest
from strip_ansi import strip_ansi

from pyway.migrate import Migrate
from pyway.configfile import ConfigFile

DBFILE = "./unittest-python-migrate.sqlite"


def make_config(migration_dir: str) -> ConfigFile:
    config = ConfigFile()
    config.database_type = "sqlite"
    config.database_name = DBFILE
    config.database_table = "pyway"
    config.database_migration_dir = migration_dir
    return config


@pytest.fixture
def clean_db():
    try:
        os.remove(DBFILE)
    except Exception:
        pass
    yield
    try:
        os.remove(DBFILE)
    except Exception:
        pass


@pytest.mark.migrate_test
@pytest.mark.sqlite_test
def test_python_migrations_mixed(clean_db) -> None:
    config = make_config(os.path.join('tests', 'data', 'schema-sqlite-python'))
    output = strip_ansi(Migrate(config).run())

    assert "V01_01__base_table.sql SUCCESS" in output
    assert "V01_02__python_data.py SUCCESS" in output
    assert "V01_03__async_python.py SUCCESS" in output

    conn = sqlite3.connect(DBFILE)
    assert conn.execute("SELECT data FROM python_test").fetchone()[0] == 'from_python'
    assert conn.execute("SELECT name FROM pytest_base").fetchone()[0] == 'inserted_by_python'
    assert conn.execute("SELECT data FROM async_python_test").fetchone()[0] == 'from_async_python'

    # History table records the PY extension and all versions
    rows = conn.execute("SELECT version, extension FROM pyway ORDER BY installed_rank").fetchall()
    assert rows == [('01.01', 'SQL'), ('01.02', 'PY'), ('01.03', 'PY')]
    conn.close()


@pytest.mark.migrate_test
@pytest.mark.sqlite_test
def test_python_migrations_idempotent(clean_db) -> None:
    config = make_config(os.path.join('tests', 'data', 'schema-sqlite-python'))
    _ = Migrate(config).run()
    output = strip_ansi(Migrate(config).run())
    assert "Nothing to do" in output


@pytest.mark.migrate_test
@pytest.mark.sqlite_test
def test_python_migration_missing_migrate_function(clean_db) -> None:
    config = make_config(os.path.join('tests', 'data', 'schema-sqlite-python-invalid'))
    with pytest.raises(RuntimeError) as e:
        Migrate(config).run()
    assert "must define a 'migrate(connection)' function" in str(e.value)
