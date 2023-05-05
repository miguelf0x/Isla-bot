# Tikhomirov Mikhail, V.2023
# github.com/miguelf0x

import os
from dotenv import load_dotenv
import interactions

from src import ConfigHandler
from src import UserInteraction
from src import Weather

# load .env
load_dotenv()
bot = interactions.Client(token=os.environ['DISCORD_API_TOKEN'])


@interactions.slash_command()
async def help(ctx):
    """Show help message"""
    await UserInteraction.send_help_embed(ctx)


@interactions.slash_command(
    name="man",
    description="Show command usage guide",
    options=[
        interactions.SlashCommandOption(
            name="command",
            description="Guide for this command will be shown",
            type=interactions.OptionType.STRING,
            required=True,
        ),
    ],
)
async def man(ctx, command):
    """Show command usage guide"""
    await UserInteraction.send_man_embed(ctx, command)


@interactions.slash_command(
    name="weather",
    description="Show weather at desired airport",
    options=[
        interactions.SlashCommandOption(
            name="icao",
            description="4 symbols of ICAO airport code",
            type=interactions.OptionType.STRING,
            min_length=4,
            max_length=4,
            required=True,
        ),
    ],
)
async def weather(ctx, icao):
    """Show command usage guide"""
    result = await Weather.get_weather(icao)
    await UserInteraction.send_weather_embed(ctx, result)


if __name__ == "__main__":

    # load config files from 'config' directory
    # data = ConfigHandler.load_config('config')
    # announce_interval = data["announce_interval"]

    # assign envvars and start bot

    bot.start()
