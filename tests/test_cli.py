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
