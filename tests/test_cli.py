import unittest
import json
import contextlib
import io

from subprocess import run

import wpsync
import wpsync.cli


class TestCLI(unittest.TestCase):
    def test_print_config(self):
        with contextlib.redirect_stdout(io.StringIO()) as f:
            wpsync.cli.main(["--print-config"])
        config = json.loads(f.getvalue())
        self.assertEqual(config["config"], None)
        self.assertEqual(config["print_config"], True)
        self.assertEqual(config["quiet"], False)
        self.assertEqual(config["version"], False)

    def test_print_config_version(self):
        with contextlib.redirect_stdout(io.StringIO()) as f:
            wpsync.cli.main(["--print-config", "--version"])
        config = json.loads(f.getvalue())
        self.assertEqual(config["config"], None)
        self.assertEqual(config["print_config"], True)
        self.assertEqual(config["quiet"], False)
        self.assertEqual(config["version"], True)

    def test_print_config_config(self):
        with contextlib.redirect_stdout(io.StringIO()) as f:
            wpsync.cli.main(["--print-config", "--config", "notexist.ini"])
        config = json.loads(f.getvalue())
        self.assertEqual(config["config"], "notexist.ini")
        self.assertEqual(config["print_config"], True)
        self.assertEqual(config["quiet"], False)
        self.assertEqual(config["version"], False)

    def test_print_config_quiet(self):
        with contextlib.redirect_stdout(io.StringIO()) as f:
            wpsync.cli.main(["--print-config", "--quiet"])
        config = json.loads(f.getvalue())
        self.assertEqual(config["config"], None)
        self.assertEqual(config["print_config"], True)
        self.assertEqual(config["quiet"], True)
        self.assertEqual(config["version"], False)

    def test_print_version(self):
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f:
            wpsync.cli.main(["--version"])
        stdout = stdout_f.getvalue()
        self.assertEqual(stdout.strip(), "v" + wpsync.__version__)

    def test_version_with_extra_options(self):
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f:
            with contextlib.redirect_stderr(io.StringIO()) as stderr_f:
                wpsync.cli.main(["--config=notexist.ini", "--version"])
        stderr = stderr_f.getvalue()
        self.assertRegex(stderr, r"useless additional options")
