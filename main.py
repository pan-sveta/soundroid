# This example requires the 'members' and 'message_content' privileged intents to function.
import os

from discord.ext.commands import CommandNotFound
from dotenv import load_dotenv
import discord
from discord.ext import commands

from minio import Minio
from pathlib import Path

load_dotenv()

print(os.environ.get('MINIO_HOST'))

minio_client = Minio(
    os.environ.get('MINIO_HOST'),
    access_key=os.environ.get('MINIO_ACCESS_KEY'),
    secret_key=os.environ.get('MINIO_PASSWORD')
)

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='?', intents=intents)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')


@bot.command()
async def ping(ctx):
    """Says when a member joined."""
    await ctx.send("pong")


@bot.command()
async def join(ctx, *, channel: discord.VoiceChannel):
    if ctx.voice_client is not None:
        return await ctx.voice_client.move_to(channel)

    await channel.connect()


@bot.command()
async def p(ctx, sound_name: str):
    sound_file = Path(f"{sound_name}.mp3")
    sound_location = Path("sounds/").joinpath(sound_file)

    try:
        minio_client.fget_object("sounds-bucket", str(sound_file), str(sound_location))
    except Exception as e:
        return await ctx.send(f"Sound {sound_name} not found")

    source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(str(sound_location)))
    ctx.voice_client.play(source, after=lambda e: print(f'Player error: {e}') if e else None)

    await ctx.send(f'Now playing {sound_name}')


async def ensure_voice(ctx):
    if ctx.voice_client is None:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("You are not connected to a voice channel.")
            raise commands.CommandError("Author not connected to a voice channel.")
    elif ctx.voice_client.is_playing():
        ctx.voice_client.stop()


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        await p(ctx, ctx.message.system_content[1:])
    else:
        raise error


bot.run(os.environ.get('DISCORD_BOT_TOKEN'))
