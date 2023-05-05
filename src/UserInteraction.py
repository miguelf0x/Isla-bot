import asyncio
import datetime
import json
import threading
import interactions


COMMANDS = ["weather", "help", "man"]

HELP_TEXT = (
    "`/weather` - show weather at selected airport\n"
    "`/help` - show this help message\n"
    "`/man [command]` - show command info"
)

HELP_COMMAND_USAGE = {

    "weather": "/weather (ICAO)",
    "help": "/help",
    "man": "/man (command)"

}

HELP_COMMAND_ARGS = {

    "weather": "(ICAO) - airport ICAO code, consists of 4 symbols\n"
               "         Allowed input: text\n",

    "help": "None",

    "man": "(command) - any command from /help output\n"
           "            Allowed input: text, refer to /help command output",

}

EMBED = interactions.Embed(
    title='Title',
    description='Description',
)

sleep_timer = 1
sleep_lock = threading.Lock()


async def __waitable(func):
    await asyncio.sleep(sleep_timer)
    return await func()


async def send_custom_embed(ctx, title, description, embed_type, ephemeral=False):
    match embed_type:
        case "INFO":
            color = interactions.Color.from_rgb(0, 255, 255)
        case "WARN":
            color = interactions.Color.from_rgb(252, 127, 0)
        case "CRIT":
            color = interactions.Color.from_rgb(255, 0, 0)
        case "GOOD":
            color = interactions.Color.from_rgb(0, 175, 15)
        case "MESG":
            color = interactions.Color.from_rgb(0, 48, 255)
        case _:
            color = interactions.Color.from_rgb(255, 0, 110)

    embedding = interactions.Embed(
        title=title,
        color=color,
        description=description
    )

    await __waitable(lambda: ctx.send(embeds=embedding, ephemeral=ephemeral))


async def send_error_embed(ctx, action, error):
    print(f"[ERROR]: While {action}\n{error}")
    await send_custom_embed(ctx, "Failed!", f"{action} failed: {error}", "CRIT")


async def send_success_embed(ctx, description):
    await send_custom_embed(ctx, "Success!", description, "GOOD")


async def send_working_embed(ctx, description):
    await send_custom_embed(ctx, "Working!", description, 0x12B211)


async def send_info_embed(ctx, title, description):
    await send_custom_embed(ctx, title, description, "INFO")


async def send_help_embed(ctx):
    await send_custom_embed(ctx, "Available commands", HELP_TEXT, "INFO", True)


async def send_man_embed(ctx, command: str):
    embedding = interactions.Embed(
        title="Commands",
        color=0x5865F2,
    )

    if command in COMMANDS:
        embedding.add_field("Command name", command, inline=False)
        embedding.add_field("Usage", HELP_COMMAND_USAGE[command], inline=False)
        embedding.add_field("Arguments", HELP_COMMAND_ARGS[command], inline=False)

    else:
        embedding.add_field("Command not found", "For available commands list use /help", inline=False)

    await __waitable(lambda: ctx.send(embeds=embedding, ephemeral=True))


async def send_weather_embed(ctx, data):

    print(json.dumps(data))

    try:
        data = data.get("data")[0]
    except IndexError as exception:
        await send_error_embed(ctx, "Weather receiving", "server has not returned any data")
        return

    station = data.get("station")
    airport_location = station.get("location")
    airport_name = station.get("name")

    embedding = interactions.Embed(
        title=f"Current weather at {airport_name}",
        color=0x5865F2,
    )

    location_text = f"Location: {airport_location}"
    elevation = data.get("elevation")
    if elevation is not None:
        elevation_ft = elevation.get("feet")
        elevation_m = elevation.get("meters")

        location_text += "\nElevation: "
        if elevation_ft is not None:
            location_text += f" {elevation_ft} ft"
        if elevation_m is not None:
            location_text += f" [{elevation_m} m]"

    embedding.add_field("Location", location_text, inline=False)

    observation_text = ""
    observation_date_raw = data.get("observed")
    observation_date_formatted = datetime.datetime.strptime(observation_date_raw,
                                                            "%Y-%m-%dT%H:%M:%S")
    current_utc_date = datetime.datetime.utcnow()
    date_diff = current_utc_date - observation_date_formatted
    diff_hours = divmod(date_diff.seconds, 3600)
    diff_minutes = divmod(diff_hours[1], 60)
    diff_seconds = diff_minutes[1]
    diff_minutes = diff_minutes[0]
    diff_hours = diff_hours[0]

    if diff_hours != 0:
        observation_text += f"[{diff_hours} h, "
    if observation_text == "":
        observation_text += f"[{diff_minutes} m, "
    else:
        observation_text += f"{diff_minutes} m, "
    observation_text += f"{diff_seconds} s back]"

    embedding.add_field("Observed at", f"{data.get('observed')} {observation_text}", inline=False)

    wind = data.get("wind")
    wind_text = f"{wind.get('degrees')}° at {wind.get('speed_kts')} kts [{wind.get('speed_mps')} m/s]"
    embedding.add_field("Wind", wind_text, inline=False)

    visibility = data.get("visibility")
    visibility_text = f"{visibility.get('miles')} miles [{visibility.get('meters')} m]"
    embedding.add_field("Visibility", visibility_text, inline=False)

    conditions = data.get("conditions")
    if conditions is not None:
        conditions_text = ""
        for i in conditions:
            conditions_text += i.get("text")
        embedding.add_field("Conditions", conditions_text, inline=False)
    else:
        print("[INFO] No conditions were received")

    ceiling = data.get("ceiling")
    if ceiling is not None:
        ceiling_text = ""

        if isinstance(ceiling, dict):

            if ceiling_text == "":
                ceiling_text += f"{ceiling.get('text')}"
            else:
                ceiling_text += "\n"
            ceiling_base_ft = ceiling.get('base_feet_agl')
            ceiling_base_m = ceiling.get('base_meters_agl')
            ceiling_ft = ceiling.get('feet')
            ceiling_m = ceiling.get('meters')
            if ceiling_base_ft is not None and ceiling_ft is not None and ceiling_base_ft != ceiling_ft:
                ceiling_text += f" from {ceiling_base_ft} ft"
                if ceiling_base_m is not None:
                    ceiling_text += f" [{ceiling_base_m} m]"
                ceiling_text += f" to {ceiling_ft} ft"
                if ceiling_m is not None and ceiling_base_m != ceiling_m:
                    ceiling_text += f" [{ceiling_m} m]"
            else:
                ceiling_text += f" at {ceiling_base_ft} ft"
                if ceiling_base_m is not None:
                    ceiling_text += f" [{ceiling_base_m} m]"

        else:

            for i in ceiling:

                if ceiling_text == "":
                    ceiling_text += f"{i.get('text')}"
                else:
                    ceiling_text += f"\n{i.get('text')}"
                ceiling_base_ft = i.get('base_feet_agl')
                ceiling_base_m = i.get('base_meters_agl')
                ceiling_ft = i.get('feet')
                ceiling_m = i.get('meters')
                if ceiling_base_ft is not None and ceiling_ft is not None and ceiling_base_ft != ceiling_ft:
                    ceiling_text += f" from {ceiling_base_ft} ft"
                    if ceiling_base_m is not None:
                        ceiling_text += f" [{ceiling_base_m} m]"
                    ceiling_text += f" to {ceiling_ft} ft"
                    if ceiling_m is not None and ceiling_base_m != ceiling_m:
                        ceiling_text += f" [{ceiling_m} m]"
                else:
                    ceiling_text += f" at {ceiling_base_ft} ft"
                    if ceiling_base_m is not None:
                        ceiling_text += f" [{ceiling_base_m} m]"

        embedding.add_field("Ceiling", ceiling_text, inline=False)
    else:
        print("[INFO] No ceiling were received")

    clouds = data.get("clouds")
    if clouds is not None:
        clouds_text = ""

        for i in clouds:
            if i.get('text') == "Clear skies":
                clouds_text = "Clear skies"
            else:
                if clouds_text == "":
                    clouds_text += f"{i.get('text')}"
                else:
                    clouds_text += f"\n{i.get('text')}"
                clouds_base_ft = i.get('base_feet_agl')
                clouds_base_m = i.get('base_meters_agl')
                clouds_ft = i.get('feet')
                clouds_m = i.get('meters')

                if clouds_base_ft is not None and clouds_ft is not None and clouds_base_ft != clouds_ft:
                    clouds_text += f" from {clouds_base_ft}"
                    if clouds_base_m is not None:
                        clouds_text += f" [{clouds_base_m} m]"
                    clouds_text += f" to {clouds_ft}"
                    if clouds_m is not None and clouds_base_m != clouds_m:
                        clouds_text += f" [{clouds_m} m]"
                else:
                    clouds_text += f" at {clouds_base_ft} ft"
                    if clouds_base_m is not None:
                        clouds_text += f" [{clouds_base_m} m]"

        embedding.add_field("Clouds", clouds_text, inline=False)
    else:
        print("[INFO] No clouds were received")

    temp_text = ""

    temperature = data.get("temperature")
    if temperature is None:
        temp_text += "Temperature unknown"
    else:
        temp_text += f"Temperature {temperature.get('celsius')}℃"

    dewpoint = data.get("dewpoint")
    if dewpoint is not None:
        temp_text += f", dewpoint {dewpoint.get('celsius')}℃"

    windchill = data.get("windchill")
    if windchill is not None:
        temp_text += f"\nWindchill {windchill.get('celsius')}℃"

    embedding.add_field("Temperature", temp_text, inline=False)

    barometer_text = ""
    barometer = data.get("barometer")
    barometer_hg = barometer.get('hg')
    barometer_hpa = barometer.get('hpa')

    if barometer_hg is not None:
        barometer_text += f" {barometer_hg} inHg"
    if barometer_hpa is not None:
        barometer_text += f" [{barometer_hpa} hPa]"

    embedding.add_field("Barometer", barometer_text, inline=False)

    raw_text = data.get("raw_text")
    report_info = ""
    footer_text = ""

    if "NOSIG" in raw_text:
        footer_text = "No significant change is expected to reported conditions within the next 2 hours"
    elif "BECMG" in raw_text:
        footer_text = "Significant stable change is expected to reported conditions within the next 2 hours"
    elif "TEMPO" in raw_text:
        footer_text = "Temporary fluctuations are expected to reported conditions within the next 2 hours"

    if footer_text != "":
        embedding.set_footer(footer_text)

    if "AUTO" in raw_text:
        report_info += "Fully Automated Report"

    if "AO1" in raw_text:
        report_info += "Automated station without precipitation discriminator"

    if "AO2" in raw_text:
        report_info += "Automated station with precipitation discriminator"

    if report_info != "":
        embedding.add_field("Report info", report_info, inline=False)

    await __waitable(lambda: ctx.send(embeds=embedding))
