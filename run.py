import argparse
import os
import shared_funcs
import shutil
import signal
import subprocess
import sys
import yaml

def gen_supervisor_conf(filename, realfilename):
    '''For the passed in config filename, generate a supervisord config file.
    
    Parameters:
        filename (str): Filename without extension.
        realfilename (str): Full path to filename.'''
    shared_funcs.write('supervisor_configs/{}.{}'.format(filename, 'ini'), '''
[program:{}]
command = {} {} {}
directory = {}
    '''.format(filename, sys.executable, os.getcwd() + '/panopticon.py', '-c ' + realfilename, os.getcwd()))

print('---------')
print('Panopticon supervisord starter.')
print('---------')

if os.path.isfile('/tmp/supervisord-panopticon.pid'):
    with open('/tmp/supervisord-panopticon.pid') as pidfile:
        os.kill(int(pidfile.readline()), signal.SIGTERM)
    print('Killed running supervisord process')
    print('---------')

print('Cleaning up old configs...')
try:
    shutil.rmtree('supervisor_configs')
except FileNotFoundError:
    pass

print('---------')
print('Generating new configs...')
for filename in os.listdir('configs'):
    if filename.endswith('.yaml'):
        gen_supervisor_conf(os.path.splitext(filename)[0], os.getcwd() + '/configs/' + filename)
        print('Generated config for {}'.format(os.path.splitext(filename)[0]))

print('---------')
print('Launching supervisord...')

process = subprocess.Popen(['supervisord', '-c', 'supervisord.conf'])
process.wait()

print('Supervisord succesfully started. You can use supervisorctl to manage supervisord.')