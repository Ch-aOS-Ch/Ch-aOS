#!/usr/bin/env python
from omegaconf import OmegaConf
import os
import subprocess

conf = {
    'pacotes': [
        'neovim',
        'git',
        'zsh',
        'htop'
    ],
    'users': [
        {
            'name': 'devuser',
            'shell': 'zsh',
            'groups': ['wheel']
        }
    ],
}

try:
    hostname = subprocess.check_output(['hostname']).decode().strip()
    if 'Dionysus' in hostname:
        conf['pacotes'].extend([
            'kitty',
            'sway'
        ])
        conf['services'] = [{'name': 'swaync'}]
        conf['hostname'] = 'dev-desktop'
    else:
        conf['hostname'] = 'dev-generic'
except Exception:
    conf['hostname'] = 'dev-fallback'


final_conf = OmegaConf.create(conf)
print(OmegaConf.to_yaml(final_conf))
