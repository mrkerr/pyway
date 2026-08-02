import asyncio
import importlib.util
import inspect
import os
import sys
from types import ModuleType
from typing import List

from pyway.helpers import Utils
from pyway.log import logger
from pyway.migration import Migration
from pyway.dbms.database import factory
from pyway.errors import MIGRATIONS_NOT_FOUND
from pyway.helpers import bcolors
from pyway.configfile import ConfigFile


class Migrate():

    def __init__(self, args: ConfigFile) -> None:
        self._db = factory(args.database_type)(args)
        self.migration_dir = args.database_migration_dir
        self.args = args

    def run(self) -> str:
        output = ''
        migrations_to_be_executed = self._get_migration_files_to_be_executed()
        if not migrations_to_be_executed:
            output += Utils.color("Nothing to do\n", bcolors.FAIL)
            return output

        for migration in migrations_to_be_executed:
            output += Utils.color(f"Migrating --> {migration.name}\n", bcolors.OKBLUE)
            try:
                if migration.extension == 'PY':
                    self._execute_python_migration(migration)
                else:
                    self._execute_sql_migration(migration)
                self._db.upgrade_version(migration)
                output += Utils.color(f"{migration.name} SUCCESS\n", bcolors.OKBLUE)
            except Exception as error:
                # Report the migrations that already succeeded before failing
                if output:
                    logger.info(output)
                raise RuntimeError(f"{migration.name} FAILED: {error}") from error
        return output

    def _execute_sql_migration(self, migration: Migration) -> None:
        with open(os.path.join(os.getcwd(),
                  self.migration_dir, migration.name), "r", encoding='utf-8') as sqlfile:
            self._db.execute(sqlfile.read())

    def _execute_python_migration(self, migration: Migration) -> None:
        # Migrations may import sibling modules from the migration directory
        migration_basepath = Utils.basepath(self.migration_dir)
        sys.path.insert(0, migration_basepath)
        try:
            module = self._load_python_migration(migration)
            connection = self._db.connect()
            try:
                if inspect.iscoroutinefunction(module.migrate):
                    asyncio.run(module.migrate(connection))
                else:
                    module.migrate(connection)
                connection.commit()
            finally:
                connection.close()
        finally:
            sys.path.remove(migration_basepath)

    def _load_python_migration(self, migration: Migration) -> ModuleType:
        migration_path = os.path.join(Utils.basepath(self.migration_dir), migration.name)
        module_name = f"pyway_migration_{migration.version.replace('.', '_')}"
        spec = importlib.util.spec_from_file_location(module_name, migration_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Could not load Python migration: {migration.name}")
        module = importlib.util.module_from_spec(spec)
        # Don't litter the migration directory with __pycache__
        dont_write_bytecode = sys.dont_write_bytecode
        sys.dont_write_bytecode = True
        try:
            spec.loader.exec_module(module)
        finally:
            sys.dont_write_bytecode = dont_write_bytecode
        if not callable(getattr(module, 'migrate', None)):
            raise RuntimeError(f"Python migration {migration.name} must define a 'migrate(connection)' function")
        return module

    def _get_migration_files_to_be_executed(self) -> List[Migration]:
        all_local_migrations = self._get_all_local_migrations()
        all_db_migrations = Migration.from_list(self._db.get_all_schema_migrations())

        if all_db_migrations and not all_local_migrations:
            raise RuntimeError(MIGRATIONS_NOT_FOUND % self.migration_dir)
        return Utils.subtract(all_local_migrations, all_db_migrations)

    def _get_all_local_migrations(self) -> List[Migration]:
        local_files = Utils.get_local_files(self.migration_dir)
        if not local_files:
            return []
        migrations = [Migration.from_name(local_file, self.migration_dir) for local_file in local_files]
        return Utils.sort_migrations_list(migrations)
