"""
Entrypoint module, in case you use `python -m pybel`

Why does this file exist, and why __main__? For more info, read:

 - https://www.python.org/dev/peps/pep-0338/
 - https://docs.python.org/2/using/cmdline.html#cmdoption-m
 - https://docs.python.org/3/using/cmdline.html#cmdoption-m
"""

import logging
import os
import time

from .cli import main

if __name__ == '__main__':
    log = logging.getLogger('pybel')
    log.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    if not os.path.exists(os.path.expanduser('~/.pybel')):
        os.mkdir(os.path.expanduser('~/.pybel'))

    fh_path = os.path.expanduser(time.strftime('~/.pybel/pybel_%Y_%m_%d_%H_%M_%S.txt'))
    fh = logging.FileHandler(fh_path)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    log.addHandler(fh)

    main()
