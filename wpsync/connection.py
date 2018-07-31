import os
import shutil
from shlex import quote
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from subprocess import run
from sh import lftp, rsync, ssh
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


class Connection:
    def __init__(self, site):
        self.site = site
        self.wpsync_dir = os.path.join(site['base_dir'], 'wpsync')

    def normalise(self, path):
        return os.path.join(self.wpsync_dir, path)

    def make_wpsync_dir(self):
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
        self.rm(path)
        return r.text


class FileConnection(Connection):
    def dir_exists(self, path):
        return os.path.isdir(path)

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
              remote_path + '/', local_path)

    def mirror_r(self, local_path, remote_path):
        rsync('--recursive', '--del', '--compress',
              local_path + '/', remote_path)

    def cat(self, path):
        with open(path, 'r') as f:
            return f.read()

    def cat_r(self, path, string):
        with open(path, 'w') as f:
            return f.write(string)

    def rm(self, path):
        os.remove(path)

    def shell(self, *command):
        process = run(command, check=True, capture_output=True)
        out = process.stdout.decode('utf-8')
        err = process.stderr.decode('utf-8')
        return out + '\n' + err


class SSHConnection(Connection):
    def __init__(self, site):
        super().__init__(site)
        self.user = quote(site['user'])
        self.host = quote(site['host'])

    def ssh_do(self, command):
        return ssh(f'{self.user}@{self.host}', command)

    def dir_exists(self, path):
        res = self.ssh_do(f'test -d {quote(path)} && echo yes')
        return 'yes' in res

    def mkdir(self, path):
        self.ssh_do(f'mkdir {quote(path)}')

    def rmdir(self, path):
        self.ssh_do(f'rm -r {quote(path)}')

    def get(self, remote_path, local_path):
        scp(f'{self.user}@{self.host}:{quote(remote_path)}', local_path)

    def put(self, local_path, remote_path):
        scp(local_path, f'{self.user}@{self.host}:{quote(remote_path)}')

    def mirror(self, remote_path, local_path):
        rsync('--recursive', '--del', '--compress',
              f'{self.user}@{self.host}:{quote(remote_path)}/',
              local_path)

    def mirror_r(self, local_path, remote_path):
        rsync('--recursive', '--del', '--compress',
              local_path + '/',
              f'{self.user}@{self.host}:{quote(remote_path)}')

    def cat(self, path):
        return self.ssh_do(f'cat {quote(path)}')

    def cat_r(self, path, string):
        self.ssh_do(f'echo {quote(string)} > {quote(path)}')

    def rm(self, path):
        self.ssh_do(f'rm {quote(path)}')

    def shell(self, *command):
        return self.ssh_do(' '.join(map(quote, command)))


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
        res = self.ftp_do(f'glob --exist -d {quote(path)} && echo yes')
        return 'yes' in res

    def mkdir(self, path):
        self.ftp_do(f'mkdir -p {quote(path)}')

    def rmdir(self, path):
        self.ftp_do(f'rm -r {quote(path)}')

    def get(self, remote_path, local_path):
        self.ftp_do(f'get {quote(remote_path)} -o {quote(local_path)}')

    def put(self, local_path, remote_path):
        self.ftp_do(f'put {quote(local_path)} -o {quote(remote_path)}')

    def mirror(self, remote_path, local_path):
        wd = os.getcwd()
        os.chdir(local_path)
        self.ftp_do(f'cd {quote(remote_path)}; mirror -P')
        os.chdir(wd)

    def mirror_r(self, local_path, remote_path):
        self.ftp_do(f'mirror -epR {quote(local_path)} {quote(remote_path)}')

    def cat(self, path):
        return self.ftp_do(f'cat {quote(path)}')

    def cat_r(self, path, string):
        with NamedTemporaryFile() as tmp_file:
            tmp_file.write(string)
            self.ftp_do(f'put {quote(tmp_file.name)} -o {quote(path)}')

    def rm(self, path):
        self.ftp_do(f'rm {quote(path)}')

    def shell(self, *command):
        cmd = ' '.join(map(quote, command)).replace("'", "\\'")
        php_code = f'<?php system(\'{cmd}\');'
        print(php_code)
        return self.run_php(php_code)
