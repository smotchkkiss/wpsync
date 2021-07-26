from argparse import ArgumentParser
from typing import List


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
