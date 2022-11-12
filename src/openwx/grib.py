"""Module for handling data retrieval from grib source data."""
import asyncio
import logging
from datetime import datetime

import aiohttp

BASE_URL = "https://noaa-gfs-bdp-pds.s3.amazonaws.com"
URL_PATTERN = "/gfs.{run_date}/{run_hour:02d}/atmos/gfs.t{run_hour:02d}z.pgrb2b.0p25.f{forecast:03d}"


async def get_grib_index(run: datetime, forecast: int) -> str:
    """Fetches grib idx file for the specified run and forecast.

    Args:
        run (datetime): The desired model run date and time.
        forecast (int): The forecast hour.

    Returns:
        str: Contents of the idx file.
    """
    date_str = run.strftime("%Y%m%d")
    run_hour = run.hour

    async with aiohttp.ClientSession() as session:
        url = (
            BASE_URL
            + URL_PATTERN.format(
                run_date=date_str, run_hour=run_hour, forecast=forecast
            )
            + ".idx"
        )
        logging.info("Requesting %s", url)
        async with session.get(url) as response:
            resp_text = await response.text()

    return resp_text


async def main():
    """Main function used for easier testing in development."""
    print(await get_grib_index(run=datetime(2022, 11, 12, 0), forecast=1))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
