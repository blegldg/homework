import sqlite3

from pathlib import Path
from json import loads
from typing import List, Dict, Tuple, Any
from dataclasses import asdict

from dacite import from_dict

from ppadb.client import Client as AdbClient
from ppadb.device import Device as AdbDevice

from structs import Experiment, ExperimentTableEntry

OUT_DIR = Path('out')
EXPERIMENTS: List[dict] = []


def diffs_report(first: Experiment, second: Experiment) -> Dict[str, Tuple[Any, Any]]:
    diff_dict: Dict[str, Tuple[Any, Any]] = {}

    for key, value in asdict(first).items():
        if value != getattr(second, key):
            diff_dict[key] = (value, getattr(second, key))

    for key, value in asdict(second).items():
        if key not in diff_dict and key not in asdict(first):
            diff_dict[key] = (None, value)

    return diff_dict


def shell_bytes(device: AdbDevice, cmd, handler=None, timeout=None) -> bytes:
    """
    returns the command output without encoding it
    """
    conn = device.create_connection(timeout=timeout)

    cmd = "shell:{}".format(cmd)
    conn.send(cmd)

    if handler:
        handler(conn)
    else:
        result = conn.read_all()
        conn.close()
        return result


def connect_to_device():
    client = AdbClient(host="127.0.0.1", port=5037)
    device = client.devices()[0]
    return device


def extract_experiments(device):
    experiments_sqlite = shell_bytes(device, "cat /data/data/com.reddit.frontpage/databases/reddit_db_anonymous")
    if not OUT_DIR.is_dir():
        OUT_DIR.mkdir()
    if not (OUT_DIR / "reddit_db_anonymous").exists():
        (OUT_DIR / "reddit_db_anonymous").touch()
    with open(OUT_DIR / "reddit_db_anonymous", "rb+") as db:
        db.write(experiments_sqlite)


def load_experiments_from_database():
    con = sqlite3.connect(OUT_DIR / "reddit_db_anonymous")
    con = con.cursor()
    res = con.execute("SELECT * FROM experiments")
    experiments = []
    for experiment_entry in res.fetchall():
        experiment_entry = ExperimentTableEntry(*experiment_entry)
        experiments_json = loads(experiment_entry.experimentsJson)
        experiments += experiments_json
    return experiments


def print_diff_report(experiments):
    diff_report = diffs_report(from_dict(Experiment, experiments[0]), from_dict(Experiment, experiments[1]))
    print(diff_report)


def main():
    device = connect_to_device()
    extract_experiments(device)
    experiments = load_experiments_from_database()
    print_diff_report(experiments)


if __name__ == '__main__':
    main()
