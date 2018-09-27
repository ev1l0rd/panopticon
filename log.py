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
        filename = shared_funcs.make_filename(message)
        string = shared_funcs.make_message(message)
        shared_funcs.write(filename, string)
        if message.attachments and self.config['save_files']:
            await shared_funcs.save_files(message, filename)

    async def on_message_edit(self, _, message):
        if message.guild and message.guild.id in self.config['ignore_servers']:
            return
        filename = shared_funcs.make_filename(message)
        string = shared_funcs.make_message(message)
        shared_funcs.write(filename, string)

    async def on_member_join(self, member):
        if member.guild and member.guild.id in self.config['ignore_servers']:
            return
        filename = shared_funcs.make_member_filename(member, "joins-leaves")
        string = "{} {}".format(self.make_member_message(member), "Joined guild")
        shared_funcs.write(filename, string)

    async def on_member_remove(self, member):
        if member.guild and member.guild.id in self.config['ignore_servers']:
            return
        filename = shared_funcs.make_member_filename(member, "joins-leaves")
        string = "{} {}".format(self.make_member_message(member), "Left guild")
        shared_funcs.write(filename, string)

    async def on_member_ban(self, _, member):
        if member.guild and member.guild.id in self.config['ignore_servers']:
            return
        filename = shared_funcs.make_member_filename(member, "bans")
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
        filename = shared_funcs.make_member_filename(after, "guild-updates")
        for string in strings:
            shared_funcs.write(filename, string)


def setup(bot):
    bot.add_cog(Panopticon(bot))
