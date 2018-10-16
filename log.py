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
import discord
from datetime import datetime
import re
import base64
from time import timezone
import os
import logging
import shared_funcs

class Panopticon:
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config

    # This determines what changed on a member.
    # Returns two variables: needs_registering and a dict called "changed_data"
    # needs_registering is a variable that determines if the member change should be logged
    # changed_data is a dict containing the changed info with the values of:
    # - old_username = str containing new guild nickname
    # - new_username = str containing old guild nickname
    # - added_roles = list of Roles that were added
    # - deleted_roles = list of Roles that were removed
    # Each should speak for itself.
    def member_changed(self, before, after):
        needs_registering = False
        changed_data = {}
        if before.display_name != after.display_name:
            needs_registering = True
            changed_data["old_username"] = before.display_name
            changed_data["new_username"] = after.display_name
        if len(before.roles) > len(after.roles): # Roles before is larger, means user has lost a role.
            changed_data["deleted_roles"] = []
            needs_registering = True
            for role in before.roles:
                if role.id == before.guild.id: # Skip everyone role
                    continue
                if role not in after.roles:
                    changed_data["deleted_roles"].append(role)
        if len(before.roles) < len(after.roles): # Roles after is larger, meaning user gained roles.
            changed_data["added_roles"] = []
            needs_registering = True
            for role in after.roles:
                if role.id == before.guild.id: # Skip everyone role
                    continue
                if role not in before.roles:
                    changed_data["added_roles"].append(role)
        return needs_registering, changed_data


    # Variant of make_member_filename that takes an additional "guild" flag
    # Needed for on_member_unban.
    def make_member_separate_guild_filename(self, member, action, guild):
        time = datetime.utcnow()
        timestamp = time.strftime('%F')
        return "{0}/{1}-{2}/#{3}/{4}/{5}.log".format(
            self.config['log_dir'],
            shared_funcs.clean_filename(guild.name),
            guild.id,
            "guild-events",
            action,
            timestamp
        )

    # Generate a reproducible message for guild member info logging
    # Output will be similar to the other one:
    # (memberid) [21:30:00] <user#0000>
    # Note that the actual _action_ will need to be appended manually.
    # memberid is base64 encoded to make it shorter
    def make_member_message(self, member):
        time = datetime.utcnow()
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


    async def on_message(self, message):
        if message.guild and message.guild.id in self.config['ignore_servers']:
            return
        filename = shared_funcs.make_filename(message, self.bot.app_info.name, self.bot.app_info.id)
        string = shared_funcs.make_message(message)
        shared_funcs.write(filename, string)
        if message.attachments and self.config['save_files']:
            await shared_funcs.save_files(message, filename)

    async def on_message_edit(self, _, message):
        if message.guild and message.guild.id in self.config['ignore_servers']:
            return
        filename = shared_funcs.make_filename(message, self.bot.app_info.name, self.bot.app_info.id)
        string = shared_funcs.make_message(message)
        shared_funcs.write(filename, string)

    async def on_member_join(self, member):
        if member.guild and member.guild.id in self.config['ignore_servers']:
            return
        filename = shared_funcs.make_member_filename(member, "joins-leaves", self.bot.app_info.name, self.bot.app_info.id)
        string = "{} {}".format(self.make_member_message(member), "Joined guild")
        shared_funcs.write(filename, string)

    async def on_member_remove(self, member):
        if member.guild and member.guild.id in self.config['ignore_servers']:
            return
        filename = shared_funcs.make_member_filename(member, "joins-leaves", self.bot.app_info.name, self.bot.app_info.id)
        string = "{} {}".format(self.make_member_message(member), "Left guild")
        shared_funcs.write(filename, string)

    async def on_member_ban(self, _, member):
        if member.guild and member.guild.id in self.config['ignore_servers']:
            return
        filename = shared_funcs.make_member_filename(member, "bans", self.bot.app_info.name, self.bot.app_info.id)
        string = "{} {}".format(self.make_member_message(member), "Was banned from guild")
        shared_funcs.write(filename, string)

    async def on_member_unban(self, guild, member):
        if guild and guild.id in self.config['ignore_servers']:
            return
        filename = self.make_member_separate_guild_filename(member, "bans", guild)
        string = "{} {}".format(self.make_member_message(member), "Was unbanned from guild")
        shared_funcs.write(filename, string)

    async def on_member_update(self, before, after):
        if before.guild and before.guild.id in self.config['ignore_servers']:
            return
        needs_registering, changed_data = self.member_changed(before, after)
        if not needs_registering:
            return
        strings = []
        prefix = self.make_member_message(after)
        if "old_username" in changed_data:
            strings.append("{} {} {} {}".format(prefix, changed_data["old_username"], "is now known under the username", changed_data["new_username"]))
        if "added_roles" in changed_data:
            strings.append("{} {} {}".format(prefix, "Got the following roles added:", shared_funcs.stringify_roles(changed_data["added_roles"])))
        if "deleted_roles" in changed_data:
            strings.append("{} {} {}".format(prefix, "Got the following roles removed:", shared_funcs.stringify_roles(changed_data["deleted_roles"])))
        filename = shared_funcs.make_member_filename(after, "guild-updates", self.bot.app_info.name, self.bot.app_info.id)
        for string in strings:
            shared_funcs.write(filename, string)


def setup(bot):
    bot.add_cog(Panopticon(bot))
