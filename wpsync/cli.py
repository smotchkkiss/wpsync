import json
import sys

from argparse import ArgumentParser, Namespace
from typing import List, NamedTuple, Optional

from crayons import blue, cyan, yellow, red, green, ColoredString

import wpsync


def main(argv: List[str]):
    args = parse_args(argv)

    if args.print_config:
        print(json.dumps(vars(args)))
        return 0

    printer = Printer(args.quiet)

    if args.version:
        print("v" + wpsync.__version__)
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


def parse_args(argv: List[str]):

    main_parser = ArgumentParser(
        prog="wpsync",
        description="Synchronise WordPress sites across ssh, (s)ftp and local hosts",
        allow_abbrev=False,
    )
    main_parser.add_argument(
        "-V", "--version", action="store_true", help="output version number"
    )
    # NOTE I never use this
    main_parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="don't print anything to STDOUT",
    )
    # NOTE I never use this
    main_parser.add_argument(
        "-c", "--config", help="use the config file specified"
    )
    main_parser.add_argument(
        "-P",
        "--print-config",
        action="store_true",
        help="print configuration and exit",
    )

    subparsers = main_parser.add_subparsers()

    sync_parser = subparsers.add_parser(
        "sync", aliases=("s"), help="sync one installation to another"
    )
    sync_parser.add_argument(
        "-d", "--database", action="store_true", help="sync the database"
    )
    sync_parser.add_argument(
        "-u", "--uploads", action="store_true", help="sync the uploads folder"
    )
    sync_parser.add_argument(
        "-p",
        "--plugins",
        action="store_true",
        help="sync the plugins directory",
    )
    sync_parser.add_argument(
        "-t", "--themes", action="store_true", help="sync the themes"
    )
    sync_parser.add_argument(
        "-a", "--all", action="store_true", help="sync all the things"
    )
    sync_parser.add_argument(
        "-f",
        "--full",
        action="store_true",
        help="sync the database and the complete WordPress installation",
    )
    sync_parser.set_defaults(subcommand="sync")

    backup_parser = subparsers.add_parser(
        "backup", aliases=("b"), help="create a backup of an installation"
    )
    backup_parser.add_argument(
        "-d", "--database", action="store_true", help="backup the database"
    )
    backup_parser.add_argument(
        "-u",
        "--uploads",
        action="store_true",
        help="backup the uploads folder",
    )
    backup_parser.add_argument(
        "-p",
        "--plugins",
        action="store_true",
        help="backup the plugins directory",
    )
    backup_parser.add_argument(
        "-t", "--themes", action="store_true", help="backup the themes"
    )
    backup_parser.add_argument(
        "-a", "--all", action="store_true", help="backup all the things"
    )
    backup_parser.add_argument(
        "-f",
        "--full",
        action="store_true",
        help="backup the database and the complete WordPress installation",
    )
    backup_parser.set_defaults(subcommand="backup")

    restore_parser = subparsers.add_parser(
        "restore", aliases=("r"), help="restore a backup into an installation"
    )
    restore_parser.add_argument(
        "-d", "--database", action="store_true", help="restore the database"
    )
    restore_parser.add_argument(
        "-u",
        "--uploads",
        action="store_true",
        help="restore the uploads folder",
    )
    restore_parser.add_argument(
        "-p",
        "--plugins",
        action="store_true",
        help="restore the plugins directory",
    )
    restore_parser.add_argument(
        "-t", "--themes", action="store_true", help="restore the themes"
    )
    restore_parser.add_argument(
        "-a", "--all", action="store_true", help="restore all the things"
    )
    restore_parser.add_argument(
        "-f",
        "--full",
        action="store_true",
        help="restore the database and the complete WordPress installation",
    )
    restore_parser.set_defaults(subcommand="restore")

    list_parser = subparsers.add_parser(
        "list", aliases=("l"), help="list existing backups"
    )
    list_parser.add_argument(
        "-d",
        "--database",
        action="store_true",
        help="list backups containing the database",
    )
    list_parser.add_argument(
        "-u",
        "--uploads",
        action="store_true",
        help="list backups containing the uploads folder",
    )
    list_parser.add_argument(
        "-p",
        "--plugins",
        action="store_true",
        help="list backups containing the plugins directory",
    )
    list_parser.add_argument(
        "-t",
        "--themes",
        action="store_true",
        help="list backups containing the themes",
    )
    list_parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="list backups containing all of these things",
    )
    list_parser.add_argument(
        "-f",
        "--full",
        action="store_true",
        help="list full backups",
    )
    list_parser.set_defaults(subcommand="list")

    install_parser = subparsers.add_parser(
        "install", aliases=("i"), help="install new WordPress at site"
    )
    install_parser.set_defaults(subcommand="install")

    args = main_parser.parse_args(argv)
    return args


class Printer:
    def __init__(self, quiet):
        self.quiet = quiet

    def format(self, string, always=False, bold=False):
        return ColoredString("RESET", string, always_color=always, bold=bold)

    def print(self, formatted_string, stderr=False):
        if not stderr and not self.quiet:
            print(formatted_string)
        if stderr:
            print(formatted_string, file=sys.stderr)

    def title(self, message):
        self.print(f'{blue("➙")} {self.format(message, bold=True)}')

    def step(self, message):
        self.print(self.format(f"• {message}"))

    def error(self, message):
        self.print(f'{red("✗")} {red(message, bold=True)}', stderr=True)

    def warn(self, message):
        self.print(f'{yellow("⚠")} {self.format(message)}', stderr=True)

    def info(self, message):
        self.print(f'{self.format("ℹ")} {self.format(message)}')

    def success(self, message):
        self.print(f'{green("✔")} {self.format(message, bold=True)}')


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
