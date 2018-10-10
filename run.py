#!/usr/bin/env python3

import discord
from discord.ext import commands
import yaml
import logging.config
import argparse

'''
Panopticon by Megumi Sonoda

Copyright (c) 2018, Valentijn "ev1l0rd" V.
All rights reserved.

Copyright 2016, Megumi Sonoda
This file is licensed under the BSD 3-clause License


Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the <organization> nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help='Config file location.', default=None)
    return parser.parse_args()

arguments = parse_arguments()

logging.basicConfig(format='%(asctime)s - [%(levelname)s] %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': True, })

# Import configuration
if not arguments.config:
    try:
        config = yaml.safe_load(open('config.yaml'))
    except Exception as e:
        raise e
else:
    try:
        config = yaml.safe_load(open(arguments.config))
    except Exception as e:
        raise e

print('Starting panopticon')

client = commands.Bot(self_bot=not config['bot_account'], 
    command_prefix=config['prefix'] if config['commands_enabled'] else 'thisaintacommandbotandshouldneverbe')
if not config['commands_enabled']:
    client.remove_command('help')
client.config = config


@client.event
async def on_ready():
    print('Succesfully started panopticon')
    print('------------')
    print('Logged in as:')
    print(client.user.name)
    print(client.user.id)
    print('------------')
    if not config['commands_enabled']:
        client.load_extension("log")
    if config['commands_enabled']:
        client.load_extension('logexisting')

# Run client
client.run(config['token'], bot=config['bot_account'], max_messages=7500, status=discord.Status.invisible)
