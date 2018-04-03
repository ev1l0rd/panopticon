#!/usr/bin/env python3

'''
Panopticon by Megumi Sonoda
Copyright 2016, Megumi Sonoda
This file is licensed under the BSD 3-clause License
'''

import base64
from datetime import timezone
import os
import re
import discord
import yaml

# Import configuration
config = yaml.safe_load(open('config.yaml'))

print('Starting panopticon')


# This sanitizes an input string to remove characters that aren't valid
#   in filenames. There are a lot of other bad filenames that can appear,
#   but given the predictable nature of our input in this application,
#   they aren't handled here.
def clean_filename(string):
    return re.sub(r'[/\\:*?"<>|\x00-\x1f]', '', string)


# This builds the relative file path & filename to log to,
#   based on the channel type of the message.
# It is affixed to the log directory set in config.py
def make_filename(message):
    if message.edited_at:
        time = message.edited_at
    else:
        time = message.created_at
    timestamp = time.strftime('%F')
    if type(message.channel) is discord.TextChannel:
        return "{}/{}-{}/#{}-{}/{}.log".format(
            config['log_dir'],
            clean_filename(message.guild.name),
            message.guild.id,
            clean_filename(message.channel.name),
            message.channel.id,
            timestamp
        )
    elif type(message.channel) is discord.DMChannel:
        return "{}/DM/{}-{}/{}.log".format(
            config['log_dir'],
            clean_filename(message.channel.user.name),
            message.channel.user.id,
            timestamp
        )
    elif type(message.channel) is discord.GroupChannel:
        return "{}/DM/{}-{}/{}.log".format(
            config['log_dir'],
            clean_filename(message.channel.name),
            message.channel.id,
            timestamp
        )


# Uses a Message object to build a very pretty string.
# Format:
#   (messageid) [21:30:00] <user#0000> hello world
# Message ID will be base64-encoded since it becomes shorter that way.
# If the message was edited, prefix messageid with E:
#   and use the edited timestamp and not the original.
def make_message(message):
    message_id = '[E:' if message.edited_at else '['
    message_id += "{}]".format(base64.b64encode(
        int(message.id).to_bytes(8, byteorder='little')
    ).decode('utf-8'))
    if message.edited_at:
        time = message.edited_at
    else:
        time = message.created_at
    if config['use_localtime']:
        time = time.replace(tzinfo=timezone.utc).astimezone(tz=None)

    timestamp = time.strftime('[%H:%M:%S]')
    author = "<{}#{}>".format(
        message.author.name,
        message.author.discriminator
    )
    content = message.clean_content.replace('\n', '\n(newline) ')

    attachments = ''
    if message.attachments:
        for attach in message.attachments:
            attachments += '\n(attach) {0[url]}'.format(attach)

    return("{} {} {} {} {}".format(
        message_id,
        timestamp,
        author,
        content,
        attachments
    ))


# Append to file, creating path if necessary
def write(filename, string):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'a', encoding='utf8') as file:
        file.write(string + "\n")


client = discord.Client()


@client.event
async def on_message(message):
    if message.guild and message.guild.id in config['ignore_servers']:
        return
    filename = make_filename(message)
    string = make_message(message)
    write(filename, string)
    print(string)

@client.event
async def on_message_edit(_, message):
    if message.guild and message.guild.id in config['ignore_servers']:
        return
    filename = make_filename(message)
    string = make_message(message)
    write(filename, string)
    print(string)

@client.event
async def on_ready():
    print('Succesfully started panopticon')
    print('------------')
    print('Logged in as:')
    print(client.user.name)
    print(client.user.id)
    print('------------')

# Run client
client.run(config['token'], bot=config['bot_account'], max_messages=7500)
