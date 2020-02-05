import json
import sqlparse
from .persistent_dict import PersistentDict


class HostInfo(PersistentDict):
    """
    HostInfo is just a PersistentDict, except that it has some
    magic items that may be retrieved without having been set
    (only "database_settings", at the moment)
    """

    def __init__(self, wpsyncdir, site, connection):
        self.wpsyncdir = wpsyncdir
        self.site = site
        self.connection = connection
        filename = site["fs_safe_name"] + ".json"
        super().__init__(wpsyncdir / "info" / filename)

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError as key_error:
            if key == "database_settings":
                self._get_database_settings()
                return self["database_settings"]
            else:
                raise key_error

    def _get_database_settings(self):
        site_backup_dir = self.wpsyncdir / "backups" / self.site["fs_safe_name"]
        last_database_backup = None
        if not site_backup_dir.is_dir():
            raise RuntimeError("No database backup to parse settings from")
        backups = sorted(site_backup_dir.iterdir())
        backups.reverse()
        for backup in backups:
            backup_db_file = backup / "database" / "dump.sql"
            if backup_db_file.is_file():
                last_database_backup = backup_db_file
                break
        if not last_database_backup:
            raise RuntimeError("No database backup to parse settings from")
        self["database_settings"] = self._parse_database_settings(
            last_database_backup
        )

    def _parse_database_settings(self, dump_file):
        to_find = ["CHARSET", "COLLATE", "ENGINE"]
        db_dump = dump_file.read_text(encoding="utf-8")
        statements = sqlparse.parse(db_dump)
        detected_keyword = None
        settings = {}
        for statement in statements:

            # only look at CREATE statements to find stuff
            if statement.token_first().value == "CREATE":
                for token in statement.flatten():
                    if token.value in to_find:
                        detected_keyword = token.value
                    elif (
                        detected_keyword
                        and token.ttype == sqlparse.tokens.Token.Name
                    ):
                        settings[detected_keyword] = token.value
                        to_find.remove(detected_keyword)
                        if len(to_find) == 0:
                            return settings
                        detected_keyword = None
        return settings
