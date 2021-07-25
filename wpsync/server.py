from datetime import datetime
from pathlib import Path
from random import choices
from string import ascii_letters, digits, punctuation, Template
import bcrypt
import requests


PASSWORD_LENGTH = 32


def install_server(connection, host_info):
    if "server_filename" not in host_info:
        server_filename = f"_wpsync_{int(datetime.now().timestamp())}.php"
        server_remote_path = connection.normalise(server_filename)
        server_code, server_password = generate_server()
        connection.cat_r(server_remote_path, server_code)
        host_info["server_filename"] = server_filename
        host_info["server_password"] = server_password


def run_server_command(site, host_info, command, **addnl_data):
    server_url = site["base_url"]
    if server_url[-1] != "/":
        server_url += "/"
    server_url += host_info["server_filename"]
    data = {
        "password": host_info["server_password"],
        "command": command,
        "db_host": site["mysql_host"],
        "db_port": site["mysql_port"],
        "db_user": site["mysql_user"],
        "db_pass": site["mysql_pass"],
        "db_name": site["mysql_name"],
    }
    data.update(addnl_data)
    r = requests.post(server_url, data=data)
    if r.status_code != 200:
        raise RemoteExecutionError(r.text.strip())
    return r.text


def generate_server():
    lib_mysqldump = slurp("Mysqldump.php")
    lib_mysqlimport = slurp("import-sql-database-mysql.php")
    lib_srdb = slurp("srdb.class.php")
    wpsync_server = slurp("wpsync_server.php")
    template_str = slurp("server_template.php")
    template = Template(template_str)
    password = generate_password(PASSWORD_LENGTH)
    password_hash = get_hash(password)
    # hash will be inserted into PHP inside single quotes
    pw_hash_esc_single_quotes = password_hash.replace(r"'", r"\'")
    code = template.substitute(
        generation_date=datetime.now().strftime("%Y-%m-%d, %H:%M"),
        lib_mysqldump=lib_mysqldump,
        lib_mysqlimport=lib_mysqlimport,
        lib_srdb=lib_srdb,
        wpsync_server=wpsync_server,
        password_hash=pw_hash_esc_single_quotes,
    )
    return code, password


def slurp(path):
    with open(Path(__file__).parent / path, "r", encoding="utf8") as f:
        return f.read()


def generate_password(length):
    chars = ascii_letters + digits + punctuation
    password = "".join(choices(chars, k=length))
    return password


def get_hash(password):
    pw_bytes = password.encode("utf8")
    pw_hash = bcrypt.hashpw(pw_bytes, bcrypt.gensalt()).decode("utf8")
    return pw_hash
