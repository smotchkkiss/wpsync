import json
import sys

from argparse import Namespace
from typing import List, NamedTuple, Optional

import wpsync

from wpsync.cli.args import parse_args
from wpsync.cli.printer import Printer


def main(argv: List[str]):
    args = parse_args(argv)

    if args.print_config:
        print(json.dumps(vars(args)))
        return 0

    printer = Printer(args.quiet)

    if args.version:
        print("v" + wpsync.VERSION)
        if (
            args.config
            or args.print_config
            or args.quiet
            or "subcommand" in args
        ):
            printer.warn("useless additional options with version switch")
            return 1
        return 0

    # TODO check existence of external executables
    # (or eliminate need for them)
    # - but maybe do it later when we know exactly which we're
    # going to need for the command executed?
    # NOTE: no, on second thought I think it may be a better idea
    # to only hint at the required external executables (and known-
    # -to-work versions) in the installation instructions instead
    # of checking for everything every single time. if a subprocess
    # call fails, we can still print a message about dependencies
    # again.

    # TODO get config
    # TODO validate config

    # TODO find the wpsync dir

    # TODO whatever `get_options` used to do?

    # TODO convert config: copy aliased entries --
    # or maybe do this after loading?
    # >> also bail if an alias would overwrite an existing entry!!!

    # TODO add config, config path, wpsyncdir and "options" to args
    # (or use another way to pass them to the function)

    if "func" not in args:
        # TODO bail if no subcommand was called --
        # I guess args.func wouldn't be set then?
        print("y u no call subcommand")
        return 1
    args.func(args)
    # TODO in the jeweilig functions:
    # validate --arguments (combinations of them)
    # interpret positional args


def cli_sync(args: Namespace) -> None:
    print("-> ZYNC")


def cli_backup(args: Namespace) -> None:
    print("--- BACKup")


def cli_restore(args: Namespace) -> None:
    print("Re[store]")


def cli_list_backups(args: Namespace) -> None:
    print("LiBa")


def cli_install(args: Namespace) -> None:
    print("insti insti clik klikc")


##########
# CONFIG #
##########


class Config:
    config_file_names = [
        "wpsync.ini",
        "wpsync.config.ini",
        ".wpsyncrc",
        ".wpsync.ini",
        ".wpsync.config.ini",
        ".wpsync/wpsync.ini",
        ".wpsync/wpsync.config.ini",
    ]

    @staticmethod
    def read_file(path):
        with open(path) as f:
            return f.read()


def get_config(path):
    config_raw = None

    if path is not None:
        try:
            config_raw = read_file(path)
        except FileNotFoundError:
            raise ConfigurationError(f"No config file found at {path}")
    else:
        # make a list of possible config file paths
        cwd = Path.cwd()
        home = Path.home()
        dirs = [d for d in [cwd, *cwd.parents] if d not in home.parents]
        if home not in dirs:
            dirs.append(home)
        for path in (d / f for d in dirs for f in config_file_names):
            try:
                config_raw = read_file(path)
                break
            except FileNotFoundError:
                pass

    if config_raw is None:
        raise ConfigurationError("No config file found")

    config = ConfigParser()
    config.read(config_raw)
    # TODO validate config
    # defaults = validate_config_default(config._defaults)
    # valid_config = validate_config_sections(config._sections)
    # normalized_config = normalize_config(valid_config, defaults)
    return (normalized_config, p)


class ConfigurationError(Exception):
    pass


class SiteNameConfiguration(NamedTuple):
    name: str
    alias: Optional[str] = None


class URLConfiguration:
    def __init__(self, site_url: str, file_url: Optional[str] = None):
        self._site_url = self.trim_trailing_slashes(site_url)
        if file_url is None:
            self._file_url = site_url
        else:
            self._file_url = self.trim_trailing_slashes(file_url)

    @property
    def site_url(self):
        return self._site_url

    @property
    def file_url(self):
        return self._file_url

    @staticmethod
    def trim_trailing_slashes(url):
        while len(url) and url[-1] == "/":
            url = url[:-1]
        return url


class BaseDirConfiguration:
    def __init__(self, base_dir: str):
        while len(base_dir) and base_dir[-1] == "/":
            base_dir = base_dir[:-1]
        self._base_dir = base_dir

    @property
    def base_dir(self):
        return self._base_dir


class ConnectionConfiguration:
    def __init__(
        self,
        protocol: str,
        username: Optional[str] = None,
        host: Optional[str] = None,
        password: Optional[str] = None,
    ):
        if protocol == "file":
            if (
                username is not None
                or host is not None
                or password is not None
            ):
                raise ConfigurationError(
                    "Can't use user/host/password with file protocol"
                )
        elif protocol == "ftp" or protocol == "sftp":
            if username is None:
                raise ConfigurationError(f"Specify {protocol} user")
            if host is None:
                raise ConfigurationError(f"Specify {protocol} host")
            if password is None:
                raise ConfigurationError(f"Specify {protocol} password")
        elif protocol == "ssh":
            if username is None:
                raise ConfigurationError("Specify ssh user")
            if host is None:
                raise ConfigurationError("Specify ssh host")
            if password is not None:
                raise ConfigurationError(
                    "SSH with password is not supported;"
                    " Set up public key authentication or use sftp"
                )
        else:
            raise ConfigurationError(f"Unknwon protocol: {protocol}")

        self._protocol = protocol
        self._username = username
        self._host = host
        self._password = password

    @property
    def protocol(self):
        return self._protocol

    @property
    def username(self):
        return self._username

    @property
    def host(self):
        return self._host

    @property
    def password(self):
        return self._password


class DatabaseConfiguration(NamedTuple):
    name: str
    host: str
    username: str
    password: str
    port: Optional[str] = None
    prefix: str = "wp_"


class HttpBasicAuthConfiguration(NamedTuple):
    username: str
    password: str


class MisbehavedHostConfiguration(NamedTuple):
    no_verify_ssl: bool = False
    sudo_remote: bool = False
    chown_remote: Optional[str] = None
    chgrp_remote: Optional[str] = None


class SiteConfiguration(NamedTuple):
    site_name: SiteNameConfiguration
    url: URLConfiguration
    base_dir: BaseDirConfiguration
    connection: ConnectionConfiguration
    database: DatabaseConfiguration
    http_basic_auth: Optional[HttpBasicAuthConfiguration] = None
    misbehaved_host: MisbehavedHostConfiguration = (
        MisbehavedHostConfiguration()
    )


def backup(installation):
    pass


def sync():
    pass


def restore():
    pass


def list_backups():
    pass


def install():
    pass


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
