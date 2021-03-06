# Contains meta/shared functions for both log.py and logexisting.py
import base64
import logging
import re
import discord
import yaml
from datetime import datetime
import os

config = yaml.safe_load(open('config.yaml'))


# This function stringifies roles.
# Param: roles = List of roles to turn into a string
# Returns str
def stringify_roles(roles):
    role_str = ""
    length = len(roles)
    for idx, role in enumerate(roles):
        role_str += role.name
        if idx != length - 1: # idx starts at 0
            role_str += ", "
    return role_str

# This stores all attachments on a message in the following structure:
#   path_to_log_file/messageid/attachment
async def save_files(message, filename):
    base_path = filename.replace('.log','/{}/'.format(message.id))
    os.makedirs(os.path.dirname(base_path), exist_ok=True)
    for attach in message.attachments:
        try:
            await attach.save(fp=base_path + attach.filename)
        except Exception as e:
            logging.error('Could not store attachment: {}'.format(e))

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
    year = time.strftime('%Y')
    month = time.strftime('%m')
    day = time.strftime('%F')
    if type(message.channel) is discord.TextChannel:
        return "{}/{}-{}/#{}-{}/{}/{}/{}.log".format(
            config['log_dir'],
            clean_filename(message.guild.name),
            message.guild.id,
            clean_filename(message.channel.name),
            message.channel.id,
            year,
            month,
            day
        )
    elif type(message.channel) is discord.DMChannel:
        return "{}/DM/{}-{}/{}/{}/{}.log".format(
            config['log_dir'],
            clean_filename(message.channel.recipient.name),
            message.channel.recipient.id,
            year,
            month,
            day
        )
    elif type(message.channel) is discord.GroupChannel:
        return "{}/DM/{}-{}/{}/{}/{}.log".format(
            config['log_dir'],
            clean_filename(message.channel.name),
            message.channel.id,
            year,
            month,
            day
        )

# This builds the relative file path & filename to log to,
# It is affixed to the log directory set in config.py
# Optionally can accept an action param for a subfolder.
def make_member_filename(member, action):
    time = datetime.utcnow()
    timestamp = time.strftime('%F')
    return "{0}/{1}-{2}/#{3}/{4}/{5}.log".format(
        config['log_dir'],
        clean_filename(member.guild.name),
        member.guild.id,
        "guild-events",
        action,
        timestamp
    )

# Dissects an embed for title, description and fields.
# Returns a string in the following format:
# (embed) ----
# (embed) Title
# (embed) ----
# (embed) Description
# (embed) ----
def dissect_embed(embed):
    dissected_embed = '\n(embed) ----'
    if embed.title:
        dissected_embed += '\n(embed) {embed.title}'
        dissected_embed += '\n(embed) ----'
    if embed.description:
        dissected_embed += '\n(embed) {embed.description}'
        dissected_embed += '\n(embed) ----'      
    return dissected_embed      

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

    timestamp = time.strftime('[%H:%M:%S]')
    author = "<{}#{}>".format(
        message.author.name,
        message.author.discriminator
    )
    content = message.clean_content.replace('\n', '\n(newline) ')

    attachments = ''
    if message.attachments:
        for attach in message.attachments:
            attachments += '\n(attach) {0}'.format(attach.url)

    embeds = ''
    if message.embeds:
        for embed in message.embeds:
            embeds += dissect_embed(embed)

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
    logging.debug("{} - {}".format(filename, string))