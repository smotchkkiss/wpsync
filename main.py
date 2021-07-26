"entry point for command line script"

import sys

from wpsync.cli.__main__ import main

sys.exit(main(sys.argv[1:]))
