import os
import shutil
from shlex import quote
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from pathlib import Path
from subprocess import run, PIPE
from sh import rsync, scp, ssh, ErrorReturnCode_1
import requests


@contextmanager
def connect(site):
    if site["protocol"] == "file":
        connection = FileConnection(site)
    elif site["protocol"] in ["ftp", "sftp"]:
        connection = FTPConnection(site)
    else:
        connection = SSHConnection(site)
    connection.make_wpsync_dir()
    yield connection
    connection.remove_wpsync_dir()


# a helper function for dealing with different forms of paths
def s(path):
    if type(path) == str:
        return path
    return str(path.resolve())


class RemoteExecutionError(Exception):
    pass


class Connection:
    def __init__(self, site):
        self.site = site
        self.wpsync_dir = site["base_dir"] + "wpsync"

    def normalise(self, path):
        return f"{self.wpsync_dir}/{s(path)}"

    def make_wpsync_dir(self):
        # TODO better to ask forgiveness
        if not self.dir_exists(self.wpsync_dir):
            self.mkdir(self.wpsync_dir)

    def remove_wpsync_dir(self):
        self.rmdir(self.wpsync_dir)

    def cat_r(self, path, string):
        tmp_file = Path(NamedTemporaryFile().name)
        tmp_file.write_text(string, encoding="utf-8")
        self.put(tmp_file, path)
        tmp_file.unlink()

    def run_php(self, php_code):
        path = self.normalise("run.php")
        url = self.site["file_url"]
        if url[-1] != "/":
            url += "/"
        url += "wpsync/run.php"
        self.cat_r(path, php_code)
        if "http_user" in self.site:
            auth = (self.site["http_user"], self.site["http_pass"])
        else:
            auth = None

        # trust selfsigned certificate if exists, needed for SSL
        # connections to localhost
        if (
            self.site["protocol"] == "file"
            and "_default_local_selfsigned_ca" in self.site
        ):
            verify = self.site["_default_local_selfsigned_ca"]
        elif self.site['no_verify_ssl']:
            verify = False
        else:
            verify = None

        r = requests.get(url, auth=auth, verify=verify)
        if r.status_code != 200:
            raise RemoteExecutionError(r.text.strip())
        self.rm(path)
        return r.text


class FileConnection(Connection):
    def dir_exists(self, path):
        return os.path.isdir(path)

    def file_exists(self, path):
        return os.path.isfile(path)

    def mkdir(self, path):
        try:
            os.mkdir(path, mode=0o755)
        except FileExistsError:
            pass

    def rmdir(self, path):
        shutil.rmtree(path)

    def get(self, remote_path, local_path):
        shutil.copyfile(remote_path, local_path)

    def put(self, local_path, remote_path):
        shutil.copyfile(local_path, remote_path)

    def mirror(self, remote_path, local_path):
        rsync(
            "--recursive",
            "--del",
            "--compress",
            remote_path + "/",
            s(local_path),
        )

    def mirror_r(self, local_path, remote_path, exclude=[]):
        args = ["--recursive", "--del", "--compress"]
        for pattern in exclude:
            args.append(f"--exclude={quote(pattern)}")
        args.extend([s(local_path) + "/", s(remote_path)])
        rsync(*args)

    def cat(self, path):
        with open(path, "r") as f:
            return f.read()

    def rm(self, path):
        os.remove(path)


class SSHConnection(Connection):
    def __init__(self, site):
        super().__init__(site)
        self.user = quote(site["user"])
        self.host = quote(site["host"])

    def ssh_do(self, command):
        if self.site['sudo_remote']:
            process = run(['ssh', '-t', f'{self.user}@{self.host}', 'sudo ' + command])
        else:
            process = run(['ssh', f'{self.user}@{self.host}', command])
        return process

    def dir_exists(self, path):
        process = self.ssh_do(f'test -d {quote(s(path))}')
        return process.returncode == 0

    def file_exists(self, path):
        process = self.ssh_do(f'test -f {quote(s(path))}')
        return process.returncode == 0

    def mkdir(self, path):
        self.ssh_do(f"mkdir {quote(s(path))}")
        if 'chown_remote' in self.site and 'chgrp_remote' in self.site:
            owner = self.site['chown_remote']
            group = self.site['chgrp_remote']
            self.ssh_do(f'chown {quote(owner)}:{quote(group)} {quote(s(path))}')
        elif 'chown_remote' in self.site:
            owner = self.site['chown_remote']
            self.ssh_do(f'chown {quote(owner)} {quote(s(path))}')
        elif 'chgrp_remote' in self.site:
            group = self.site['chgrp_remote']
            self.ssh_do(f'chgrp {quote(group)} {quote(s(path))}')

    def rmdir(self, path):
        self.ssh_do(f"rm -r {quote(s(path))}")

    def get(self, remote_path, local_path):
        options = ['--compress']
        if self.site['sudo_remote']:
            options.append('--rsync-path=sudo rsync')
        run([
            'rsync',
            *options,
            f'{self.user}@{self.host}:{quote(s(remote_path))}',
            s(local_path),
        ])

    def put(self, local_path, remote_path):
        options = ['--compress']
        if self.site['sudo_remote']:
            options.append('--rsync-path=sudo rsync')
        run([
            'rsync',
            *options,
            s(local_path),
            f'{self.user}@{self.host}:{quote(s(remote_path))}',
        ])
        if 'chown_remote' in self.site and 'chgrp_remote' in self.site:
            owner = self.site['chown_remote']
            group = self.site['chgrp_remote']
            self.ssh_do(f'chown {quote(owner)}:{quote(group)} {quote(s(remote_path))}')
        elif 'chown_remote' in self.site:
            owner = self.site['chown_remote']
            self.ssh_do(f'chown {quote(owner)} {quote(s(remote_path))}')
        elif 'chgrp_remote' in self.site:
            group = self.site['chgrp_remote']
            self.ssh_do(f'chgrp {quote(group)} {quote(s(remote_path))}')

    def mirror(self, remote_path, local_path):
        options = ['--recursive', '--del', '--compress']
        if self.site['sudo_remote']:
            options.append('--rsync-path=sudo rsync')
        run([
            'rsync',
            *options,
            f'{self.user}@{self.host}:{quote(s(remote_path))}/',
            s(local_path),
        ])

    def mirror_r(self, local_path, remote_path, exclude=[]):
        args = ["--recursive", "--del", "--compress"]
        for pattern in exclude:
            args.append(f"--exclude={quote(pattern)}")
        if self.site['sudo_remote']:
            args.append('--rsync-path=sudo rsync')
        args.append(s(local_path) + "/")
        args.append(f"{self.user}@{self.host}:{quote(s(remote_path))}")
        run(['rsync', *args])
        if 'chown_remote' in self.site and 'chgrp_remote' in self.site:
            owner = self.site['chown_remote']
            group = self.site['chgrp_remote']
            self.ssh_do(f'chown -R {quote(owner)}:{quote(group)} {quote(s(path))}')
        elif 'chown_remote' in self.site:
            owner = self.site['chown_remote']
            self.ssh_do(f'chown -R {quote(owner)} {quote(s(path))}')
        elif 'chgrp_remote' in self.site:
            group = self.site['chgrp_remote']
            self.ssh_do(f'chgrp -R {quote(group)} {quote(s(path))}')

    def cat(self, path):
        return self.ssh_do(f"cat {quote(s(path))}")

    def rm(self, path):
        self.ssh_do(f"rm {quote(s(path))}")


class FTPConnection(Connection):
    def __init__(self, site):
        super().__init__(site)
        self.user = quote(site["user"])
        self.pasw = quote(site["pass"])
        if site["protocol"] == "sftp":
            self.host = quote("sftp://" + site["host"])
        else:
            self.host = quote(site["host"])

    def lftp(self, command, capture=False):
        completed_process = run(
            [
                "lftp",
                "-c",
                f"open -u {self.user},{self.pasw} {self.host}; {command}; quit",
            ],
            stdout=PIPE,
            stderr=PIPE,
        )
        if completed_process.stdout:
            return completed_process.stdout.decode("utf8")
        return ""

    def dir_exists(self, path):
        path = path[:-1] + "[" + path[-1] + "]"
        res = self.lftp(
            f"glob --exist -d {quote(s(path))} && echo yes", capture=True
        )
        return "yes" in res

    def file_exists(self, path):
        path = path[:-1] + "[" + path[-1] + "]"
        res = self.lftp(
            f"glob --exist -f {quote(s(path))} && echo yes", capture=True
        )
        return "yes" in res

    def mkdir(self, path):
        self.lftp(f"mkdir -p {quote(s(path))}")

    def rmdir(self, path):
        self.lftp(f"rm -r {quote(s(path))}")

    def get(self, remote_path, local_path):
        self.lftp(f"get {quote(s(remote_path))} -o {quote(s(local_path))}")

    def put(self, local_path, remote_path):
        self.lftp(f"put {quote(s(local_path))} -o {quote(s(remote_path))}")

    def mirror(self, remote_path, local_path):
        cmd = "mirror --delete"
        self.lftp(f"{cmd} {quote(s(remote_path))} {quote(s(local_path))}")

    def mirror_r(self, local_path, remote_path, exclude=[]):
        cmd = "mirror --delete -R"
        for pattern in exclude:
            cmd += f" --exclude {quote(pattern)}"
        cmd += f" {quote(s(local_path))} {quote(s(remote_path))}"
        self.lftp(cmd)

    def cat(self, path):
        return self.lftp(f"cat {quote(s(path))}", capture=True)

    def rm(self, path):
        self.lftp(f"rm {quote(s(path))}")
