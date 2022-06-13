import asyncio
from datetime import datetime, timedelta

from mawaqit import MawaqitClient


USERNAME = ""
PASSWORD = ""
latitude = "45.764043"
longitude = "4.835659"
token= ''
mosque_id=''

async def main() -> None:
    async with MawaqitClient(latitude, longitude, mosque_id, USERNAME, PASSWORD, token ) as client:
        api = await client.apimawaqit()
        print(api)
        da = await client.all_mosques_neighberhood()
        for i in range(len(da)):
            print(da[i]["uuid"])
        db = await client.fetch_prayer_times()
        print (db)


asyncio.run(main())     







