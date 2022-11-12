"""Module for handling data retrieval from grib source data."""
import asyncio
import logging
from datetime import datetime
from typing import Optional

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


def parse_grib_index(index: str) -> dict[str, dict[str, dict[str, Optional[int]]]]:
    """Parses a grib index file into a usable dictionary.

    Args:
        index (str): The contents of the grib index file.

    Returns:
        dict[str, dict[str, dict[str, Optional[int]]]]: A dictionary containing parameter, level,
            and start/stop byte addresses.
    """
    result = {}
    prev_start = None
    for line in index.split("\n")[::-1]:
        if len(line) != 0:
            _, start, _, parameter, level, _ = line.rstrip(":").split(":")
            stop = prev_start - 1 if prev_start is not None else None
            byte_locations = {"start": int(start), "stop": stop}
            if parameter in result.keys():
                result[parameter][level] = byte_locations
            else:
                result[parameter] = {level: byte_locations}

            prev_start = int(start)
    return result


async def main():
    """Main function used for easier testing in development."""
    print(
        parse_grib_index(
            await get_grib_index(run=datetime(2022, 11, 12, 0), forecast=1)
        )
    )


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
