from configparser import ConfigParser

import requests
from requests_file import FileAdapter


def download_url(url):
    """Downloads and parses a config file from url"""
    session = requests.Session()
    if url.startswith('file://'):
        session.mount('file://', FileAdapter())
    res = session.get(url)

    lines = [line.decode('utf-8', errors='ignore').strip() for line in res.iter_lines()]

    value_line = 1 + max(i for i, line in enumerate(lines) if '[Values]' == line.strip())

    metadata_config = ConfigParser()
    metadata_config.optionxform = lambda option: option
    metadata_config.read_file(lines[:value_line ])

    delimiter = metadata_config['Processing']['DelimiterString']

    value_dict = {}
    for line in lines[value_line:]:
        sline = line.rsplit(delimiter, 1)
        key = sline[0].strip()

        value_dict[key] = sline[1].strip() if len(sline) == 2 else None

    res = {}
    res.update({k: dict(v) for k, v in metadata_config.items()})
    res['Values'] = value_dict

    return res