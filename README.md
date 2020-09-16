# wpsync

Sync WordPress installations across local, ftp, sftp and ssh hosts

**NOTE:** I changed the name of the default branch from `master` to `main`. To reflect the changes in your local repository, run the following commands:
```sh
git fetch --all
git remote set-head origin -a
git branch --set-upstream-to origin/main
git branch -m master main
```

## Installation

wpsync uses the [pipenv](https://pipenv.pypa.io/) package/dependency manager, so make sure you have it installed.

Then:

```sh
git clone https://github.com/em4nl/wpsync.git
cd wpsync
pipenv install
```

Now you should be able to run wpsync from its own directory with `poetry run wpsync`.

To make it accessible from everywhere, I usually make a shell script that I place in `~/bin/wpsync`:

```sh
#!/bin/sh

# change the path to wherever you cloned wpsync to.
# the $@ in the end passes your arguments through to wpsync
cd "$HOME/wpsync" && pipenv run wpsync $@
```

Don't forget to make the script executable (`chmod +x ~/bin/wpsync`)!

(I use this workaround because I have no idea how to install a python package properly.)

## License

This project contains some (PHP) code from different third parties that is subject to different licenses. The rest of the code that is mine I intend to put under the MIT license. I'll have to sort this out.
