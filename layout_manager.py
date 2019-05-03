#!/bin/python3

import json
import os
import subprocess
import re

LANG = 'en-GB'
TEXT = json.loads(open('i18n/{}.json'.format(LANG), 'r').read())
LAYOUT_PATH = '~/.config/i3/layouts'

os.system('mkdir -p {} > /dev/null 2>&1'.format(LAYOUT_PATH))

workspaces_resp = subprocess.Popen(['i3-msg', '-t', 'get_workspaces'],
                                   stdout=subprocess.PIPE).stdout.read().decode("utf-8")
workspaces = json.loads(workspaces_resp)

for workspace in workspaces:
    if workspace['focused']:
        current_workspace = workspace
        break

containers_resp = subprocess.Popen(['i3-save-tree', '--workspace',
                                    str(current_workspace['num'])], stdout=subprocess.PIPE).stdout.read().decode("utf-8")
for arg in ['class', 'instance', 'title', 'window_role']:
    containers_resp = containers_resp.replace(
        '// "{}"'.format(arg), '  "{}"'.format(arg))

containers_resp = '\n'.join([re.sub(r'//.*', '', line)
                             for line in containers_resp.split('\n')][1:])
containers = [container_resp for container_resp in containers_resp.split(
    '\n\n') if container_resp != '']
containers = [json.loads(container)
              for container in containers]

print(containers)
