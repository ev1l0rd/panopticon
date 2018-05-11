'''
Panopticon by Megumi Sonoda
Copyright 2016, Megumi Sonoda
This file is licensed under the BSD 3-clause License

Fork License:
Copyright (c) 2018, Valentijn "ev1l0rd" V.
All rights reserved.

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
import discord
import datetime
import re
import base64
from time import timezone
import os
import logging


class Panopticon:
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config

    # This sanitizes an input string to remove characters that aren't valid
    #   in filenames. There are a lot of other bad filenames that can appear,
    #   but given the predictable nature of our input in this application,
    #   they aren't handled here.
    def clean_filename(self, string):
        return re.sub(r'[/\\:*?"<>|\x00-\x1f]', '', string)

    # This builds the relative file path & filename to log to,
    #   based on the channel type of the message.
    # It is affixed to the log directory set in config.py
    def make_filename(self, message):
        if message.edited_at:
            time = message.edited_at
        else:
            time = message.created_at
        timestamp = time.strftime('%F')
        if type(message.channel) is discord.TextChannel:
            return "{}/{}-{}/#{}-{}/{}.log".format(
                self.config['log_dir'],
                self.clean_filename(message.guild.name),
                message.guild.id,
                self.clean_filename(message.channel.name),
                message.channel.id,
                timestamp
            )
        elif type(message.channel) is discord.DMChannel:
            return "{}/DM/{}-{}/{}.log".format(
                self.config['log_dir'],
                self.clean_filename(message.channel.user.name),
                message.channel.user.id,
                timestamp
            )
        elif type(message.channel) is discord.GroupChannel:
            return "{}/DM/{}-{}/{}.log".format(
                self.config['log_dir'],
                self.clean_filename(message.channel.name),
                message.channel.id,
                timestamp
            )

    # This builds the relative file path & filename to log to,
    # It is affixed to the log directory set in config.py
    def make_member_filename(self, member):
        if self.config['use_localtime']:
            time = datetime.now()
        else:
            time = datetime.utcnow()
        timestamp = time.strftime('%F')
        return "{0}/{1}-{2}/#{3}/{4}.log".format(
            self.config['log_dir'],
            self.clean_filename(member.guild.name),
            member.guild.id,
            "guild-events",
            timestamp
        )

    # Uses a Message object to build a very pretty string.
    # Format:
    #   (messageid) [21:30:00] <user#0000> hello world
    # Message ID will be base64-encoded since it becomes shorter that way.
    # If the message was edited, prefix messageid with E:
    #   and use the edited timestamp and not the original.
    def make_message(self, message):
        message_id = '[E:' if message.edited_at else '['
        message_id += "{}]".format(base64.b64encode(
            int(message.id).to_bytes(8, byteorder='little')
        ).decode('utf-8'))
        if message.edited_at:
            time = message.edited_at
        else:
            time = message.created_at
        if self.config['use_localtime']:
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
                attachments += '\n(attach) {0}'.format(attach.url)

        return("{} {} {} {} {}".format(
            message_id,
            timestamp,
            author,
            content,
            attachments
        ))

    # Generate a reproducible message for guild member info logging
    # Output will be similar to the other one:
    # (memberid) [21:30:00] <user#0000>
    # Note that the actual _action_ will need to be appended manually.
    # memberid is base64 encoded to make it shorter
    def make_member_message(self, member):
        if self.config['use_localtime']:
            time = datetime.now()
        else:
            time = datetime.utcnow()
        if self.config['use_localtime']:
            time = time.replace(tzinfo=timezone.utc).astimezone(tz=None)
        timestamp = time.strftime('[%H:%M:%S]')

        member_name = "<{}#{}>".format(
            member.name,
            member.discriminator
        )

        member_id = "[{}]".format(base64.b64encode(
            int(member.id).to_bytes(8, byteorder='little')
        ).decode('utf-8'))

        return ("{} {} {} ").format(
            member_id,
            timestamp,
            member_name
        )

    # Append to file, creating path if necessary
    def write(self, filename, string):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'a', encoding='utf8') as file:
            file.write(string + "\n")
        logging.debug("{} - {}".format(filename, string))

    async def on_message(self, message):
        if message.guild and message.guild.id in self.config['ignore_servers']:
            return
        filename = self.make_filename(message)
        string = self.make_message(message)
        self.write(filename, string)

    async def on_message_edit(self, _, message):
        if message.guild and message.guild.id in self.config['ignore_servers']:
            return
        filename = self.make_filename(message)
        string = self.make_message(message)
        self.write(filename, string)

    async def on_member_join(self, member):
        if member.guild and member.guild.id in self.config['ignore_servers']:
            return
        filename = self.make_member_filename(member)
        string = "{} {}".format(self.make_member_message(member), "Joined guild")
        self.write(filename, string)

    async def on_member_remove(self, member):
        if member.guild and member.guild.id in self.config['ignore_servers']:
            return
        filename = self.make_member_filename(member)
        string = "{} {}".format(self.make_member_message(member), "Left guild")
        self.write(filename, string)

    async def on_member_ban(self, member):
        if member.guild and member.guild.id in self.config['ignore_servers']:
            return
        filename = self.make_member_filename(member)
        string = "{} {}".format(self.make_member_message(member), "Was banned from guild")
        self.write(filename, string)

    async def on_member_unban(self, member):
        if member.guild and member.guild.id in self.config['ignore_servers']:
            return
        filename = self.make_member_filename(member)
        string = "{} {}".format(self.make_member_message(member), "Was unbanned from guild")
        self.write(filename, string)


def setup(bot):
    bot.add_cog(Panopticon(bot))
