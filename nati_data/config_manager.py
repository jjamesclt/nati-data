import os
import configparser
import pymysql
import random


def get_random_working_db_host(hosts_csv: str, fallback_host: str, port: int, user: str, password: str, database: str) -> str:
    """Returns the first working host from shuffled list."""
    hosts = [h.strip() for h in hosts_csv.split(',') if h.strip()]
    if fallback_host and fallback_host not in hosts:
        hosts.append(fallback_host)

    if not hosts:
        raise ValueError("No database hosts defined")

    random.shuffle(hosts)

    for host in hosts:
        try:
            conn = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                connect_timeout=2  # quick failure
            )
            conn.close()
            return host
        except Exception:
            continue

    raise ConnectionError(f"None of the database hosts are reachable: {hosts}")


class ConfigManager:
    def __init__(self, ini_filename='nati.ini'):
        self.ini_file = os.path.join(os.getcwd(), ini_filename)
        self.parser = configparser.ConfigParser()
        self.parser.read(self.ini_file)

        self.db_conn = None
        self.db_data = {}

    def get(self, dotted_key: str):
        try:
            module, key = dotted_key.split('.')
        except ValueError:
            raise KeyError("Key must be in the format 'module.key'")

        if module == 'database' and key == 'random':
            return self._get_random_working_host()

        if self.parser.has_option(module, key):
            return self.parser[module][key]

        return self.get_from_db(module, key)

    def _get_random_working_host(self):
        db_cfg = self.parser['database']
        return get_random_working_db_host(
            hosts_csv=db_cfg.get('hosts', ''),
            fallback_host=db_cfg.get('host', None),
            port=int(db_cfg.get('port', 3306)),
            user=db_cfg['uid'],
            password=db_cfg['pwd'],
            database=db_cfg['name']
        )

    def get_from_db(self, module: str, key: str):
        if not self.db_conn:
            self._init_db_conn()

        if not self.db_data:
            self._load_db_data()

        return self.db_data.get((module, key))

    def _init_db_conn(self):
        db_cfg = self.parser['database']
        port = int(db_cfg.get('port', 3306))
        user = db_cfg['uid']
        password = db_cfg['pwd']
        database = db_cfg['name']

        working_host = get_random_working_db_host(
            hosts_csv=db_cfg.get('hosts', ''),
            fallback_host=db_cfg.get('host', None),
            port=port,
            user=user,
            password=password,
            database=database
        )

        self.db_conn = pymysql.connect(
            host=working_host,
            port=port,
            user=user,
            password=password,
            database=database
        )

    def _load_db_data(self):
        try:
            with self.db_conn.cursor() as cursor:
                cursor.execute("SELECT config_module, config_key, config_value FROM nati_config")
                for module, key, value in cursor.fetchall():
                    self.db_data[(module, key)] = value
        except Exception as e:
            print(f"Failed to load DB config: {e}")
