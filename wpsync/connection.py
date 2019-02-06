import os
import shutil
from shlex import quote
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from pathlib import Path
from subprocess import run
from sh import lftp, rsync, scp, ssh, ErrorReturnCode_1
import requests


@contextmanager
def connect(site):
    if site['protocol'] == 'file':
        connection = FileConnection(site)
    elif site['protocol'] in ['ftp', 'sftp']:
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
        self.wpsync_dir = site['base_dir'] + 'wpsync'

    def normalise(self, path):
        return f'{self.wpsync_dir}/{s(path)}'

    def make_wpsync_dir(self):
        # TODO better to ask forgiveness
        if not self.dir_exists(self.wpsync_dir):
            self.mkdir(self.wpsync_dir)

    def remove_wpsync_dir(self):
        self.rmdir(self.wpsync_dir)

    def run_php(self, php_code):
        path = self.normalise('run.php')
        url = self.site['base_url']
        if url[-1] != '/':
            url += '/'
        url += 'wpsync/run.php'
        self.cat_r(path, php_code)
        if 'http_user' in self.site:
            auth = (self.site['http_user'], self.site['http_pass'])
        else:
            auth = None
        r = requests.get(url, auth=auth)
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
        rsync('--recursive', '--del', '--compress',
              remote_path + '/', s(local_path))

    def mirror_r(self, local_path, remote_path, exclude=[]):
        args = ['--recursive', '--del', '--compress']
        for pattern in exclude:
            args.append(f'--exclude={quote(pattern)}')
        args.extend([s(local_path) + '/', s(remote_path)])
        rsync(*args)

    def cat(self, path):
        with open(path, 'r') as f:
            return f.read()

    def cat_r(self, path, string):
        with open(path, 'w') as f:
            return f.write(string)

    def rm(self, path):
        os.remove(path)


class SSHConnection(Connection):
    def __init__(self, site):
        super().__init__(site)
        self.user = quote(site['user'])
        self.host = quote(site['host'])

    def ssh_do(self, command):
        return ssh(f'{self.user}@{self.host}', command)

    def dir_exists(self, path):
        try:
            res = self.ssh_do(f'test -d {quote(s(path))} && echo yes')
        except ErrorReturnCode_1 as e:
            return False
        return 'yes' in res

    def file_exists(self, path):
        try:
            res = self.ssh_do(f'test -f {quote(s(path))} && echo yes')
        except ErrorReturnCode_1 as e:
            return False
        return 'yes' in res

    def mkdir(self, path):
        self.ssh_do(f'mkdir {quote(s(path))}')

    def rmdir(self, path):
        self.ssh_do(f'rm -r {quote(s(path))}')

    def get(self, remote_path, local_path):
        scp(f'{self.user}@{self.host}:{quote(s(remote_path))}', s(local_path))

    def put(self, local_path, remote_path):
        scp(local_path, f'{self.user}@{self.host}:{quote(s(remote_path))}')

    def mirror(self, remote_path, local_path):
        rsync('--recursive', '--del', '--compress',
              f'{self.user}@{self.host}:{quote(s(remote_path))}/',
              s(local_path))

    def mirror_r(self, local_path, remote_path, exclude=[]):
        args = ['--recursive', '--del', '--compress']
        for pattern in exclude:
            args.append(f'--exclude={quote(pattern)}')
        args.append(s(local_path) + '/')
        args.append(f'{self.user}@{self.host}:{quote(s(remote_path))}')
        rsync(*args)

    def cat(self, path):
        return self.ssh_do(f'cat {quote(s(path))}')

    def cat_r(self, path, string):
        self.ssh_do(f'echo {quote(string)} > {quote(s(path))}')

    def rm(self, path):
        self.ssh_do(f'rm {quote(s(path))}')


class FTPConnection(Connection):
    def __init__(self, site):
        super().__init__(site)
        self.user = quote(site['user'])
        self.pasw = quote(site['pass'])
        self.host = quote(site['host'])

    def ftp_do(self, command):
        user = self.user
        pasw = self.pasw
        host = self.host
        return lftp('-c', f'open -u {user},{pasw} {host}; {command}; quit')

    def dir_exists(self, path):
        path = path[:-1] + '[' + path[-1] + ']'
        try:
            res = self.ftp_do(f'glob --exist -d {quote(s(path))} && echo yes')
        except ErrorReturnCode_1 as e:
            return False
        return 'yes' in res

    def file_exists(self, path):
        path = path[:-1] + '[' + path[-1] + ']'
        try:
            res = self.ftp_do(f'glob --exist -f {quote(s(path))} && echo yes')
        except ErrorReturnCode_1 as e:
            return False
        return 'yes' in res

    def mkdir(self, path):
        self.ftp_do(f'mkdir -p {quote(s(path))}')

    def rmdir(self, path):
        self.ftp_do(f'rm -r {quote(s(path))}')

    def get(self, remote_path, local_path):
        self.ftp_do(f'get {quote(s(remote_path))} -o {quote(s(local_path))}')

    def put(self, local_path, remote_path):
        self.ftp_do(f'put {quote(s(local_path))} -o {quote(s(remote_path))}')

    def mirror(self, remote_path, local_path):
        cmd = 'mirror --delete'
        self.ftp_do(f'{cmd} {quote(s(remote_path))} {quote(s(local_path))}')

    def mirror_r(self, local_path, remote_path, exclude=[]):
        cmd = 'mirror --delete -R'
        for pattern in exclude:
            cmd += f' --exclude {quote(pattern)}'
        cmd += f' {quote(s(local_path))} {quote(s(remote_path))}'
        self.ftp_do(cmd)

    def cat(self, path):
        return self.ftp_do(f'cat {quote(s(path))}')

    def cat_r(self, path, string):
        tmp_file = Path(NamedTemporaryFile().name)
        tmp_file.write_text(string, encoding='utf-8')
        self.ftp_do(f'put {quote(s(tmp_file))} -o {quote(s(path))}')
        tmp_file.unlink()

    def rm(self, path):
        self.ftp_do(f'rm {quote(s(path))}')
