import unittest
import json
import contextlib
import io

from subprocess import run

import wpsync.cli_new


class TestCLI(unittest.TestCase):
    def test_print_config(self):
        with contextlib.redirect_stdout(io.StringIO()) as f:
            wpsync.cli_new.main(["--print-config"])
        config = json.loads(f.getvalue())
        self.assertEqual(config["config"], None)
        self.assertEqual(config["print_config"], True)
        self.assertEqual(config["quiet"], False)
        self.assertEqual(config["version"], False)

    def test_print_config_version(self):
        with contextlib.redirect_stdout(io.StringIO()) as f:
            wpsync.cli_new.main(["--print-config", "--version"])
        config = json.loads(f.getvalue())
        self.assertEqual(config["config"], None)
        self.assertEqual(config["print_config"], True)
        self.assertEqual(config["quiet"], False)
        self.assertEqual(config["version"], True)

    def test_print_config_config(self):
        with contextlib.redirect_stdout(io.StringIO()) as f:
            wpsync.cli_new.main(
                ["--print-config", "--config", "notexist.ini"]
            )
        config = json.loads(f.getvalue())
        self.assertEqual(config["config"], "notexist.ini")
        self.assertEqual(config["print_config"], True)
        self.assertEqual(config["quiet"], False)
        self.assertEqual(config["version"], False)

    def test_print_config_quiet(self):
        with contextlib.redirect_stdout(io.StringIO()) as f:
            wpsync.cli_new.main(["--print-config", "--quiet"])
        config = json.loads(f.getvalue())
        self.assertEqual(config["config"], None)
        self.assertEqual(config["print_config"], True)
        self.assertEqual(config["quiet"], True)
        self.assertEqual(config["version"], False)

    def test_version_with_extra_options(self):
        with contextlib.redirect_stderr(io.StringIO()) as f:
            wpsync.cli_new.main(["--config=notexist.ini", "--version"])
        stderr = f.getvalue()
        self.assertRegex(stderr, r"useless additional options")
