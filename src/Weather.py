import os

import httpx
import json


class ServerError(Exception):
    __slots__ = ("code", "text")

    def __init__(self, code: int, text: str) -> None:
        super().__init__()
        self.code = code
        self.text = text

    def __str__(self) -> str:
        if self.code == -1:
            return "Error: Not connected"
        else:
            return f"Error: HTTP code {self.code}, {self.text}"


async def __decorated_requests(req_lambda) -> httpx.Response:
    try:
        res = await req_lambda()
    except Exception as e:
        if e is httpx.ConnectError:
            raise ServerError(-1, "Requested host is down")
        raise e

    if res.status_code >= 400:
        raise ServerError(res.status_code, f"Requested host reported an error: {res.text}")

    return res


async def get_weather(icao: str):
    weather_api_key = os.environ['WEATHER_API_KEY']
    request_url = f"https://api.checkwx.com/metar/{icao.upper()}/decoded?x-api-key={weather_api_key}"
    result = await httpx.AsyncClient().get(url=request_url)
    result = result.json()
    return result
