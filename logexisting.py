import discord
from discord.ext import commands
import datetime
import base64
import os
import re
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

class logExisting:
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config

    ## SECTION FOR STUFF LIFTED FROM LOG.PY

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
            time = time.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)

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

    # Dissects an embed for title, description and fields.
    # Returns a string in the following format:
    # (embed) ----
    # (embed) Title
    # (embed) ----
    # (embed) Description
    # (embed) ----
    def dissect_embed(self, embed):
        dissected_embed = '\n(embed) ----'
        if embed.title:
            dissected_embed += '\n(embed) {embed.title}'
            dissected_embed += '\n(embed) ----'
        if embed.description:
            dissected_embed += '\n(embed) {embed.description}'
            dissected_embed += '\n(embed) ----'      
        return dissected_embed

    # Append to file, creating path if necessary
    def write(self, filename, string):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'a', encoding='utf8') as file:
            file.write(string + "\n")

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
            return "{}/{}-{}/#{}-{}/{}/{}/{}.log".format(
                self.config['log_dir'],
                self.clean_filename(message.guild.name),
                message.guild.id,
                self.clean_filename(message.channel.name),
                message.channel.id,
                year,
                month,
                day
            )
        elif type(message.channel) is discord.DMChannel:
            return "{}/DM/{}-{}/{}/{}/{}.log".format(
                self.config['log_dir'],
                self.clean_filename(message.channel.recipient.name),
                message.channel.recipient.id,
                year,
                month,
                day
            )
        elif type(message.channel) is discord.GroupChannel:
            return "{}/DM/{}-{}/{}/{}/{}.log".format(
                self.config['log_dir'],
                self.clean_filename(message.channel.name),
                message.channel.id,
                year,
                month,
                day
            )

    # This sanitizes an input string to remove characters that aren't valid
    #   in filenames. There are a lot of other bad filenames that can appear,
    #   but given the predictable nature of our input in this application,
    #   they aren't handled here.
    def clean_filename(self, string):
        return re.sub(r'[/\\:*?"<>|\x00-\x1f]', '', string)

    ## COMMANDS

    @commands.command()
    async def archive_all(self, ctx):
        '''
        Archives EVERYTHING, DMs and all guilds.

        DM restrictions still apply.
        '''
        await ctx.invoke(self.bot.get_command('archive_dms'))
        await ctx.invoke(self.bot.get_command('archive_servers'))
        print('Everything has been archived!')

    @commands.command()
    async def archive_dms(self, ctx):
        '''
        Archives the last 128 DMs. 
        
        If you need DMs that are older than this, call archive_dm with the ID of the user you desire.

        This is a limitation imposed by Discord, panopticon cannot work around this.
        '''
        for channel in self.bot.private_channels:
            await ctx.invoke(self.bot.get_command('archive_channel'), channel.id) 

    @commands.command()
    async def archive_server(self, ctx, server_id: int):
        '''
        Archives the server with the passed in server ID.
        '''
        guild = self.bot.get_guild(server_id)
        print('Started archival of {}'.format(str(guild)))
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).read_messages:
                await ctx.invoke(self.bot.get_command('archive_channel'), channel.id)

    @commands.command()
    async def archive_servers(self, ctx):
        '''
        Archives all servers.
        '''
        for guild in self.bot.guilds:
            await ctx.invoke(self.bot.get_command('archive_server'), guild.id)

    @commands.command()
    async def archive_channel(self, ctx, channel_id: int):
        '''
        Archives an individual channel.

        Normally there is little reason to call this, it's usually called under the hood by the other commands.
        '''
        channel = self.bot.get_channel(channel_id)
        print('Started archival of {}'.format(str(channel)))
        store_message = []
        async for message in channel.history(limit=None, reverse=True):
            path = self.make_filename(message)
            store_message.append([path, self.make_message(message), message.created_at])

        store_message.sort(key= lambda x: x[2])
        for message in store_message:
            self.write(message[0], message[1])
        print('Succesfully archived {}'.format(str(channel)))

    @commands.command()
    async def archive_dm(self, ctx, user_id: int):
        '''
        Archives all your DMs with a user.
        '''
        channel = self.bot.get_user(user_id).dm_channel
        await ctx.invoke(self.bot.get_command('archive_channel'), channel.id)

def setup(bot):
	bot.add_cog(logExisting(bot))
