import discord
from discord.ext import commands
import datetime
import base64
import os
import re
import logging
import shared_funcs

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
            path = shared_funcs.make_filename(message, self.bot.user.name, self.bot.user.id)
            store_message.append([path, shared_funcs.make_message(message), message.created_at])
            if message.attachments and self.config['save_files']:
                await shared_funcs.save_files(message, path)

        store_message.sort(key= lambda x: x[2])
        for message in store_message:
            shared_funcs.write(message[0], message[1])

    @commands.command()
    async def archive_dm(self, ctx, user_id: int):
        '''
        Archives all your DMs with a user.
        '''
        channel = self.bot.get_user(user_id).dm_channel
        await ctx.invoke(self.bot.get_command('archive_channel'), channel.id)

def setup(bot):
	bot.add_cog(logExisting(bot))
