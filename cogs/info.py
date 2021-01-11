import discord
from typing import Optional
from utils.CustomCog import Cog
from discord.ext.commands import command, guild_only, Context
import psutil as p
import humanize
from datetime import datetime, timedelta
from time import time
import collections
import glob
import platform


class Info(Cog):
	def __init__(self, bot):
		self.bot = bot
		self.name = 'ℹ Info'
		self.status_emojis = {
			'online': '<:online:313956277808005120>',
			'idle': '<:away2:464520569862357002>',
			'dnd': '<:dnd2:464520569560498197>',
			'offline': '<:offline2:464520569929334784>'
		}

	@command()
	@guild_only()
	async def spotify(self, ctx: Context, member: Optional[discord.Member]):
		"""Spotify status command.
		Shows Spotify activity of a specified member.
		Args: member (discord.Member, optional): Member you want to see activity of.
		Takes author as target if any member not specified.
		Returns: Exception: if the member is not listening Spotify currently."""
		member = member or ctx.author
		if activity := discord.utils.find(lambda a: isinstance(a, discord.Spotify), member.activities):
			embed = self.bot.embed.default(
				ctx,
				title=f'<:spotify:585766969144508416> {activity.title}',
				description=f'**Duration:** {humanize.naturaldelta(activity.duration)}\n'
				f'**Album:** {activity.album}\n'
				f'**Artists:** {" • ".join([i for i in activity.artists])}',
				url=f'https://open.spotify.com/track/{activity.track_id}'
			).set_thumbnail(url=activity.album_cover_url)
			return await ctx.send(embed=embed)
		else:
			await ctx.send(f"**{member}** isn't Spotifying rn.")

	@command()
	async def uptime(self, ctx):
		"""Uptime command.
		Returns: uptime: How much time bot is onlin."""
		hours, remainder = divmod((await self.bot.get_uptime()), 3600)
		minutes, seconds = divmod(remainder, 60)
		days, hours = divmod(hours, 24)
		embed = self.bot.embed().add_field(
			name='Uptime',
			value=f'{days}d, {hours}h {minutes}m {seconds}s'
		)
		return await ctx.send(embed=embed)

	@command(aliases=['sys'])
	async def system(self, ctx):
		"""Information of the system that is running the bot."""
		embed = self.bot.embed(title="System Info").set_thumbnail(url="https://cdn.discordapp.com/attachments/735725378433187901/776524927708692490/data-server.png")
		pr = p.Process()
		info = {
			'System': {
				'Username': pr.as_dict(attrs=["username"])['username'],
				'Host OS': platform.platform(),
				'Uptime': timedelta(seconds=time() - p.boot_time()),
				'Boot time': datetime.fromtimestamp(p.boot_time()).strftime("%Y-%m-%d %H:%M:%S"),
			},
			'CPU': {
				'Frequency': f"{p.cpu_freq(percpu=True)[0][0]} MHz",
				'CPU Used': f"{p.cpu_percent(interval=1)}%",
				'Time on CPU': timedelta(seconds=p.cpu_times().system + p.cpu_times().user),
			},
			'Memory': {
				'RAM Used': f"{p.virtual_memory().percent}%",
				'RAM Available': f"{p.virtual_memory().available/(1024**3):,.3f} GB",
				'Disk Used': f"{p.disk_usage('/').percent}%",
				'Disk Free': f"{p.disk_usage('/').free/(1024**3):,.3f} GB",
			}
		}
		for key in info:
			embed.add_field(name=f'**> {key}**', value='\n'.join([f'**{k}:** {v}' for k, v in info[key].items()]), inline=False)
		await ctx.send(embed=embed)

	@command()
	async def codestats(self, ctx):
		"""Code statistic of the bot."""
		ctr: collections.Counter[str] = collections.Counter()
		for ctr['file'], f in enumerate(glob.glob('./**/*.py', recursive=True)):
			with open(f, encoding='UTF-8') as fp:
				for ctr['line'], line in enumerate(fp, ctr['line']):
					line = line.lstrip()
					ctr['comment'] += '#' in line
					ctr['class'] += line.startswith('class')
					ctr['function'] += line.startswith('def')
					ctr['coroutine'] += line.startswith('async def')
		await ctx.send(embed=self.bot.embed(description='\n'.join(f'{key.title()}: {value}' for key, value in ctr.items())))

	@command(aliases=['bi', 'about'])
	async def botinfo(self, ctx):
		"""See some kind of information about me (such as command usage, links etc.)"""
		servers = self.bot.guilds
		embed = self.bot.embed().set_author(name=self.bot.user.display_name, icon_url=self.bot.user.avatar_url_as(size=128))
		fields = {
			'General': {
				('Owner', f'{self.bot.dosek}'),
				('Currently in', f'{len(servers)} servers'),
				('Commands working', f'{len(self.bot.commands)}'),
				('Commands used (last restart)', self.bot.command_usage),
			},
			'Links': {
				('Invite link', f'[Here]({self.bot.invite_url})'),
				('GitHub', f'[Here]({self.bot.github_url})'),
				('Support', f'[Here]({self.bot.support_url})'),
			},
		}
		for key in fields:
			embed.add_field(name=key, value='\n'.join([f'**{name}:** {value}' for name, value in fields[key]]), inline=False)
		await ctx.send(embed=embed)

	@command(aliases=["memberinfo", "ui", "mi"])
	@guild_only()
	async def userinfo(self, ctx, member: Optional[discord.Member]):
		"""See some general information about mentioned user."""
		member = member or ctx.author
		mutual_servers = sum(1 for g in self.bot.guilds if g.get_member(ctx.author.id))
		embed = self.bot.embed(title=f'{self.status_emojis[str(member.status)]}{member.display_name}')
		embed.set_thumbnail(url=member.avatar_url)
		fields = [
			("Mutual Servers", mutual_servers, True),
			("Top role", member.top_role.mention, True),
			("Activity", f"{str(member.activity.type).split('.')[-1].title() if member.activity else 'N/A'} {member.activity.name if member.activity else ''}", True),
			("Boosted server", bool(member.premium_since), True),
			("Account created", humanize.naturaldate(member.created_at), True),
			("Here since", humanize.naturaldate(member.joined_at), True)
		]
		embed.description = '\n'.join([f'**{name}:** {value}' for name, value, inline in fields])
		await ctx.send(embed=embed)

	@command(aliases=["guildinfo", "si", "gi"])
	@guild_only()
	async def serverinfo(self, ctx):
		"""See some general information about current guild."""
		embed = self.bot.embed().set_author(
			name=ctx.guild.name,
			icon_url=ctx.guild.icon_url_as(size=128),
			url=ctx.guild.icon_url
		)
		embed.set_thumbnail(url=ctx.guild.banner_url_as(size=256))
		fields = [
			("Owner", ctx.guild.owner, True),
			("Region", ctx.guild.region, True),
			("Created", humanize.time.naturaltime(ctx.guild.created_at), True),
			("Members", ctx.guild.member_count, True),
			("Bots", sum(x.bot for x in ctx.guild.members), True),
			("Boosts", ctx.guild.premium_subscription_count, True),
			("Roles", len(ctx.guild.roles), True),
			("Text channels", len(ctx.guild.text_channels), True),
			("Voice channels", len(ctx.guild.voice_channels), True),
			("Categories", len(ctx.guild.categories), True),
		]
		embed.description = '\n'.join([f'**{n}:** {v}' for n, v, inline in fields])
		await ctx.send(embed=embed)


def setup(bot):
	bot.add_cog(Info(bot))
