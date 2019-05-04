#!/bin/python3

import time
import json
import os
import subprocess
import re


LANG = 'en-GB'
SCRIPT_DIR = os.path.dirname(__file__)


def path(file):
    return os.path.join(SCRIPT_DIR, file)


TEXT = json.loads(
    open(path('i18n/{}.json'.format(LANG)), 'r').read())
LAYOUT_PATH = '~/.config/i3/layouts'

os.system('mkdir -p {} > /dev/null 2>&1'.format(LAYOUT_PATH))

workspaces_response = subprocess.Popen(['i3-msg', '-t', 'get_tree'],
                                       stdout=subprocess.PIPE).stdout.read().decode("utf-8")

global_data = json.loads(workspaces_response)
current_workspace = None


def has_a_focused_node(node):
    if node['focused']:
        return True
    elif node.get('nodes'):
        for sub_node in node['nodes']:
            if has_a_focused_node(sub_node):
                return True

    return False


for node in global_data['nodes']:
    if node['type'] == 'output':
        for content in node['nodes']:
            if content['type'] == 'con':
                for workspace in content['nodes']:
                    if workspace['type'] == 'workspace' and has_a_focused_node(workspace):
                        current_workspace = workspace
                        break

if current_workspace is None:
    raise Exception('No focused workspace detected')

print(current_workspace)


def get_ppid(pid):
    ppid = subprocess.Popen(['ps', '-p', pid, '-o', 'ppid', '--no-headers'],
                            stdout=subprocess.PIPE).stdout.read().decode("utf-8").strip()

    # If the parent process is not the root process
    return pid if ppid == '1' else get_ppid(ppid)


def set_init_command(node):
    if node['window']:
        pid_response = subprocess.Popen(['xprop', '_NET_WM_PID', '-id', str(node['window'])],
                                        stdout=subprocess.PIPE).stdout.read().decode("utf-8")
        pid = pid_response.split(' ')[-1].replace('\n', '')
        ppid = get_ppid(pid)

        node['command'] = subprocess.Popen(['ps', '-p', ppid, '-o', 'args', '--no-headers'],
                                           stdout=subprocess.PIPE).stdout.read().decode("utf-8").replace('\n', '')

        env = subprocess.Popen(['cat', '/proc/{}/environ'.format(ppid)],
                               stdout=subprocess.PIPE).stdout.read().decode("utf-8").split('\0',)
        node['environment'] = {key: value for (
            key, value) in [elem.split('=', 1) for elem in env if elem != '']}

    elif node.get('nodes'):
        for key in range(len(node['nodes'])):
            node['nodes'][key] = set_init_command(node['nodes'][key])

    return node


def create_node(node):
    env = os.environ.copy()

    subprocess.Popen(node['command'].split(' '),
                     env={**env, **node['environment']}, shell=True)


def load_workspace(node):
    if node['window']:
        create_node(node)
    elif node.get('nodes'):
        for sub_node in node['nodes']:
            load_workspace(sub_node)


current_workspace = set_init_command(current_workspace)
file = open(path('current.json'), 'w')
file.write(json.dumps(current_workspace, sort_keys=True, indent=4))

load_workspace(current_workspace)

# containers_resp = subprocess.Popen(['i3-save-tree', '--workspace',
#                                     str(current_workspace['num'])], stdout=subprocess.PIPE).stdout.read().decode("utf-8")
# for arg in ['class', 'instance', 'title', 'window_role']:
#     containers_resp = containers_resp.replace(
#         '// "{}"'.format(arg), '  "{}"'.format(arg))
#
# containers_resp = '\n'.join([re.sub(r'//.*', '', line)
#                              for line in containers_resp.split('\n')][1:])
# containers = [container_resp for container_resp in containers_resp.split(
#     '\n\n') if container_resp != '']
# containers = [json.loads(container)
#               for container in containers]
#
# file = open('current.json', 'w')
# file.write(json.dumps(containers, sort_keys=True, indent=4))
# print(containers)
