# Contains meta/shared functions for both log.py and logexisting.py
import base64
import logging
import re
import discord
import yaml
from datetime import datetime
import os

'''
logexisting.py - Module for panopticon to log existing messages.
Copyright (C) 2018 - Valentijn V.

This file is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''
class BaseLogger():
    config = {}
    bot = None
    clean_regex = re.compile(r'[/\\:*?"<>|\x00-\x1f]')

    # This function stringifies roles.
    # Param: roles = List of roles to turn into a string
    # Returns str
    def stringify_roles(self, roles):
        role_str = ""
        length = len(roles)
        for idx, role in enumerate(roles):
            role_str += role.name
            if idx != length - 1: # idx starts at 0
                role_str += ", "
        return role_str

    # This stores all attachments on a message in the following structure:
    #   path_to_log_file/messageid/attachment
    async def save_files(self, message, filename):
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
    def clean_filename(self, string):
        return self.clean_regex.sub('', string)

    # This builds the relative file path & filename to log to,
    #   based on the channel type of the message.
    # It is affixed to the log directory set in config.py
    def make_filename(self, message):
        if message.edited_at:
            time = message.edited_at
        else:
            time = message.created_at
        year = time.strftime('%Y')
        month = time.strftime('%m')
        day = time.strftime('%F')
        if type(message.channel) is discord.TextChannel:
            return "logs/{}/{}-{}/#{}-{}/{}/{}/{}.log".format(
                '{}-{} '.format(self.clean_filename(self.bot.user.name), str(self.bot.user.id)),
                self.clean_filename(message.guild.name),
                message.guild.id,
                self.clean_filename(message.channel.name),
                message.channel.id,
                year,
                month,
                day
            )
        elif type(message.channel) is discord.DMChannel:
            return "logs/{}/DM/{}-{}/{}/{}/{}.log".format(
                '{}-{} '.format(self.clean_filename(self.bot.user.name), str(self.bot.user.id)),
                self.clean_filename(message.channel.recipient.name),
                message.channel.recipient.id,
                year,
                month,
                day
            )
        elif type(message.channel) is discord.GroupChannel:
            return "logs/{}/DM/{}-{}/{}/{}/{}.log".format(
                '{}-{} '.format(self.clean_filename(self.bot.user.name), str(self.bot.user.id)),
                self.clean_filename(message.channel.name),
                message.channel.id,
                year,
                month,
                day
            )

    # This builds the relative file path & filename to log to,
    # It is affixed to the log directory set in config.py
    # Optionally can accept an action param for a subfolder.
    def make_member_filename(self, member, action):
        time = datetime.utcnow()
        timestamp = time.strftime('%F')
        return "logs/{0}/{1}-{2}/#{3}/{4}/{5}.log".format(
            '{}-{} '.format(self.clean_filename(self.bot.user.name), str(self.bot.user.id)),
            self.clean_filename(member.guild.name),
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
    def dissect_embed(self, embed):
        dissected_embed = ['\n(embed) ----']
        if embed.title:
            dissected_embed.append(f'\n(embed) {embed.title}')
            dissected_embed.append('\n(embed) ----')
        if embed.description:
            dissected_embed.append(f'\n(embed) {embed.description}')
            dissected_embed.append('\n(embed) ----')
        return "".join(dissected_embed)

    # Uses a Message object to build a very pretty string.
    # Format:
    #   (messageid) [21:30:00] <user#0000> hello world
    # Message ID will be base64-encoded since it becomes shorter that way.
    # If the message was edited, prefix messageid with E:
    #   and use the edited timestamp and not the original.
    def make_message(self, message):
        message_id = ['[E:' if message.edited_at else '[', '{}'.format(
            base64.b64decode(
                int(message.id).to_bytes(8, byteorder='little')))]
        message_id = "".join(message_id)

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
                embeds += self.dissect_embed(embed)

        return("{} {} {} {} {}".format(
            message_id,
            timestamp,
            author,
            content,
            attachments
        ))

    # Append to file, creating path if necessary
    def write(self, filename, string):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'a', encoding='utf8') as file:
            file.write(string + "\n")
        logging.debug("{} - {}".format(filename, string))

    # Check if guild passes the config whitelist and blacklist
    # Params:
    # guild: guild to match
    # use_whitelist: check for whitelist?
    # whitelist: whitelist to match
    # use_blacklist: check for blacklist?
    # blacklist: blacklist to match
    # Returns:
    #    boolean: True if pass, false if not.
    def list_pass(self, guild: discord.Guild):
        if self.config["use_whitelist"]:
            if guild.id in self.config["whitelist"]:
                return True
            else:
                return False
        if self.config["use_blacklist"]:
            if guild.id not in self.config["blacklist"]:
                return True
            else:
                return False