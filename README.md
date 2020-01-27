# wpsync

Sync WordPress installations across local, ftp, sftp and ssh hosts

## Installation

wpsync uses the [poetry](https://python-poetry.org) package/dependency manager, so make sure you have it installed.

Then:

```sh
git clone https://github.com/em4nl/wpsync.git
cd wpsync
poetry install
```

Now you should be able to run wpsync from its own directory with `poetry run wpsync`.

To make it accessible from anywhere, I usually make a shell script that I place in `~/bin/wpsync`:

```sh
#!/bin/sh

# change the path to wherever you cloned wpsync to.
# the $@ in the end passes your arguments through to wpsync
cd "$HOME/projects/wpsync" && poetry run wpsync $@
```

Don't forget to make the script executable (`chmod +x ~/bin/wpsync`)!

(I use this workaround because I have no idea how to install a python package properly.)

## License

This project contains some (PHP) code from different third parties that is subject to different licenses. The rest of the code that is mine I intend to put under the MIT license. I'll have to sort this out.
