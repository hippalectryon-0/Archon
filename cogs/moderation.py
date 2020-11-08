import discord
from discord.ext import commands, tasks
import json
from ast import literal_eval

from rcon.commands import Rcon, RconCommandError
from rcon.instances import check_perms, is_game
from rcon.logs import ServerLogs

from utils import Config, get_player_input_type, base_embed
config = Config()



class moderation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.command(description="Warn a player", usage="r!warn <player> <reason>", aliases=["warn_player"])
    @check_perms(moderation=True)
    async def warn(self, ctx, name_or_id: str, *, reason: str):
        inst = self.bot.cache.instance(ctx.author.id).update()
        player = inst.get_player(name_or_id)
        if not player:
            raise commands.BadArgument("Player %s isn't online at the moment" % name_or_id)
        res = inst.rcon.warn(player.steam_id, reason)

        embed = base_embed(inst.id, title="Player warned", description=res)
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)
        ServerLogs(inst.id).add('rcon', f'{ctx.author.name}#{ctx.author.discriminator} warned {player.name} for "{reason}"')
    
    @commands.command(description="Kill a player and remove them from their squad", usage="r!punish <player>", aliases=["punish_player", "kill", "kill_player"])
    @check_perms(moderation=True)
    async def punish(self, ctx, name_or_id: str, *, reason: str = None):
        inst = self.bot.cache.instance(ctx.author.id).update()
        player = inst.get_player(name_or_id)
        if not player:
            raise commands.BadArgument("Player %s isn't online at the moment" % name_or_id)
        inst.rcon.change_team(player.steam_id)
        inst.rcon.change_team(player.steam_id)
        warn_reason = "You were killed by an Admin."
        if reason: warn_reason = warn_reason + " Reason: " + reason
        res = inst.rcon.warn(player.steam_id, warn_reason)

        embed = base_embed(inst.id, title="Player killed and removed from squad", description=res)
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)
        ServerLogs(inst.id).add('rcon', f'{ctx.author.name}#{ctx.author.discriminator} punished {player.name} for "{reason}"')

    @commands.command(description="Kick a player", usage="r!kick <player> [reason]", aliases=["kick_player"])
    @check_perms(moderation=True)
    async def kick(self, ctx, name_or_id: str, *, reason: str = "Kicked by a moderator"):
        inst = self.bot.cache.instance(ctx.author.id).update()
        player = inst.get_player(name_or_id)
        if not player:
            raise commands.BadArgument("Player %s isn't online at the moment" % name_or_id)
        res = inst.rcon.kick(player.steam_id, reason)
        self.bot.cache.instance(ctx.author.id).disconnect_player(player)

        embed = base_embed(inst.id, title="Player kicked", description=res)
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)
        ServerLogs(inst.id).add('rcon', f'{ctx.author.name}#{ctx.author.discriminator} kicked {player.name} for "{reason}"')

    @commands.command(description="Ban a player", usage="r!ban <player> [duration] [reason]", aliases=["ban_player"])
    @check_perms(moderation=True)
    async def ban(self, ctx, name_or_id: str, duration: str = "0", *, reason: str = "Banned by a moderator"):
        inst = self.bot.cache.instance(ctx.author.id).update()
        player = inst.get_player(name_or_id)
        if not player:
            raise commands.BadArgument("Player %s isn't online at the moment" % name_or_id)
        if "perm" in duration:
            duration = "0"
        res = inst.rcon.ban(player.steam_id, duration, reason)
        self.bot.cache.instance(ctx.author.id).disconnect_player(player)

        embed = base_embed(inst.id, title="Player banned", description=res)
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)
        ServerLogs(inst.id).add('rcon', f'{ctx.author.name}#{ctx.author.discriminator} banned {player.name} for {duration} for "{reason}"')

    @commands.command(description="Broadcast a message", usage="r!broadcast <message>", aliases=["bc"])
    @check_perms(moderation=True)
    async def broadcast(self, ctx, message: str):
        inst = self.bot.cache.instance(ctx.author.id)
        res = inst.rcon.broadcast(message)

        embed = base_embed(self.bot.cache.instance(ctx.author.id).id, title="Message broadcasted", description=res)
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)
        ServerLogs(inst.id).add('rcon', f'{ctx.author.name}#{ctx.author.discriminator} broadcasted "{message}"')


    @commands.command(description="Demote a commander (Squad only)", usage="r!demote_commander (name or id|team id) [reason]")
    @check_perms(moderation=True)
    @is_game(game="squad")
    async def demote_commander(self, ctx, name_or_id: str, *, reason: str = None):
        inst = self.bot.cache.instance(ctx.author.id).update()
        player = inst.get_player(name_or_id)
        if not player:
            raise commands.BadArgument("Player %s isn't online at the moment" % name_or_id)
        res = inst.rcon.demote_commander(player.steam_id)
        if "is not a commander" in res:
            raise RconCommandError(res)
        warn_reason = "An Admin demoted you."
        if reason: warn_reason = warn_reason + " Reason: " + reason
        inst.rcon.warn(player.steam_id, warn_reason)

        embed = base_embed(inst.id, title="Commander demoted", description=res)
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)
        ServerLogs(inst.id).add('rcon', f'{ctx.author.name}#{ctx.author.discriminator} demoted commander {player.name} for "{reason}"')
    
    @commands.command(description="Remove a player from their squad", usage="r!kick_from_squad <player>", aliases=["squad_kick", "squadkick", "remove_from_squad"])
    @check_perms(moderation=True)
    async def kick_from_squad(self, ctx, name_or_id: str, *, reason: str = None):
        inst = self.bot.cache.instance(ctx.author.id).update()
        player = inst.get_player(name_or_id)
        if not player:
            raise commands.BadArgument("Player %s isn't online at the moment" % name_or_id)
        res = inst.rcon.remove_from_squad(player.steam_id)
        if "is not in a squad" in res:
            raise RconCommandError(res)
        warn_reason = "An Admin removed you from your squad."
        if reason: warn_reason = warn_reason + " Reason: " + reason
        inst.rcon.warn(player.steam_id, warn_reason)

        embed = base_embed(inst.id, title="Player removed from squad", description=res)
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)
        ServerLogs(inst.id).add('rcon', f'{ctx.author.name}#{ctx.author.discriminator} squad-kicked {player.name} for "{reason}"')

    @commands.command(description="Force a player to switch team", usage="r!switch_team <player>", aliases=["switch_teams", "change_team", "change_teams"])
    @check_perms(moderation=True)
    async def switch_team(self, ctx, name_or_id: str, *, reason: str = None):
        inst = self.bot.cache.instance(ctx.author.id).update()
        player = inst.get_player(name_or_id)
        if not player:
            raise commands.BadArgument("Player %s isn't online at the moment" % name_or_id)
        res = inst.rcon.change_team(player.steam_id)
        warn_reason = "An Admin switched your team."
        if reason: warn_reason = warn_reason + " Reason: " + reason
        inst.rcon.warn(player.steam_id, warn_reason)

        embed = base_embed(inst.id, title="Player switched", description=res)
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)
        ServerLogs(inst.id).add('rcon', f'{ctx.author.name}#{ctx.author.discriminator} team-switched {player.name} for "{reason}"')

    @commands.command(description="Disband a squad", usage="r!disband_squad <team id> <squad id>", aliases=["disband"])
    @check_perms(moderation=True)
    async def disband_squad(self, ctx, team_id: int, squad_id: int, *, reason: str = None):
        if team_id not in range(1, 2):
            raise commands.BadArgument('team_id needs to be either 1 or 2')

        inst = self.bot.cache.instance(ctx.author.id).update()
        
        if team_id == 1: team = inst.team1
        elif team_id == 2: team = inst.team2
        squads = team.squads

        try:
            squad = [squad for squad in squads if squad.id == squad_id][0]
        except:
            raise commands.BadArgument('No squad found with this ID')

        players = inst.select(team_id=team_id, squad_id=squad_id)
        res = inst.rcon.disband_squad(team_id, squad_id)
        warn_reason = "An Admin disbanded the squad you were in."
        if reason: warn_reason = warn_reason + " Reason: " + reason
        for player in players:
            inst.rcon.warn(player.steam_id, warn_reason)

        embed = base_embed(inst.id, title="Squad disbanded", description=res)
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)
        ServerLogs(inst.id).add('rcon', f'{ctx.author.name}#{ctx.author.discriminator} disbanded {team.faction_short}/Squad{squad_id} for "{reason}"')

    
    @commands.command(description="Go to the next match", usage="r!skip_match [map name]", aliases=["skip", "end", "end_match"])
    @check_perms(moderation=True)
    async def skip_match(self, ctx, *, map_name: str = ""):
        inst = self.bot.cache.instance(ctx.author.id)
        if map_name:
            res = inst.rcon.switch_to_map(map_name)
        else:
            res = inst.rcon.end_match()

        embed = base_embed(self.bot.cache.instance(ctx.author.id).id, title="Skipped the current match", description=res)
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)
        ServerLogs(inst.id).add('rcon', f'{ctx.author.name}#{ctx.author.discriminator} skipped the current match')
    
    @commands.command(description="Restart the current match", usage="r!restart_match", aliases=["restart"])
    @check_perms(moderation=True)
    async def restart_match(self, ctx):
        inst = self.bot.cache.instance(ctx.author.id)
        res = inst.rcon.restart_match()

        embed = base_embed(self.bot.cache.instance(ctx.author.id).id, title="Restarted the current match", description=res)
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)
        ServerLogs(inst.id).add('rcon', f'{ctx.author.name}#{ctx.author.discriminator} restarted the current match')

    @commands.command(description="View or set the next map", usage="r!set_next_map [map name]", aliases=["next", "next_map", "queue", "queue_map", "view_map"])
    @check_perms(moderation=True)
    async def set_next_map(self, ctx, *, map_name: str):
        inst = self.bot.cache.instance(ctx.author.id)
        res = inst.rcon.set_next_map(map_name)

        embed = base_embed(self.bot.cache.instance(ctx.author.id).id, title="Queued the next map", description=res)
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)
        ServerLogs(inst.id).add('rcon', f'{ctx.author.name}#{ctx.author.discriminator} queued {map_name}')


def setup(bot):
    bot.add_cog(moderation(bot))