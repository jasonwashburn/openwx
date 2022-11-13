"""Module for handling data retrieval from grib source data."""
import asyncio
import logging
from datetime import datetime
from typing import Optional

import aiohttp

BASE_URL = "https://noaa-gfs-bdp-pds.s3.amazonaws.com"
URL_PATTERN = "/gfs.{run_date}/{run_hour:02d}/atmos/gfs.t{run_hour:02d}z.pgrb2b.0p25.f{forecast:03d}"


def get_grib_url(run: datetime, forecast: int) -> str:
    """Returns a formatted grib URL string from run and forecast.

    Args:
        run (datetime): Model run date and hour.
        forecast (int): Forecast hour.

    Returns:
        str: A formatted URL for the model run and forecast.
    """
    return BASE_URL + URL_PATTERN.format(
        run_date=run.strftime("%Y%m%d"), run_hour=run.hour, forecast=forecast
    )


def get_grib_idx_url(run: datetime, forecast: int) -> str:
    """Returns a formatted idx URL string from run and forecast.

    Args:
        run (datetime): Model run date and hour.
        forecast (int): Forecast hour.

    Returns:
        str: A formatted URL for the model run and forecast.
    """
    return get_grib_url(run=run, forecast=forecast) + ".idx"


async def get_grib_index(run: datetime, forecast: int) -> str:
    """Fetches grib idx file for the specified run and forecast.

    Args:
        run (datetime): The desired model run date and time.
        forecast (int): The forecast hour.

    Returns:
        str: Contents of the idx file.
    """
    async with aiohttp.ClientSession() as session:
        url = get_grib_idx_url(run=run, forecast=forecast)
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


async def get_start_stop_byte_nums(
    run: datetime, forecast: int, parameter: str, level: str
) -> Optional[tuple[Optional[int], Optional[int]]]:
    """Gets the start and stop byte numbers for a given parameter and level.

    Args:
        run (datetime): Datetime of model run.
        forecast (int): The forecast hour.
        parameter (str): The requested parameter.
        level (str): The requested level.

    Returns:
        Optional[tuple[Optional[int], Optional[int]]]: A tuple of start and stop byte nums.
    """
    index = await get_grib_index(run=run, forecast=forecast)
    parsed_index = parse_grib_index(index)
    param_dict = parsed_index.get(parameter)
    if param_dict is not None:
        start_and_stop = param_dict.get(level)
        if start_and_stop is not None:
            start_byte = start_and_stop["start"]
            stop_byte = start_and_stop["stop"]
            return start_byte, stop_byte
        else:
            logging.warning("Level: %s is not in grib index.", level)
            return None
    else:
        logging.warning("Param: %s is not in grib index.", parameter)
        return None


async def get_grib_message(run: datetime, forecast: int, parameter: str, level: str):
    """TODO Fill me in when complete."""
    # url = get_grib_url(run=run, forecast=forecast)
    # index = get_grib_index(run=run, forecast=forecast)
    # TODO Finish me.


async def main():
    """Main function used for easier testing in development."""
    parsed_index = parse_grib_index(
        await get_grib_index(run=datetime(2022, 11, 12, 0), forecast=1)
    )
    print(parsed_index)
    start_stop = await get_start_stop_byte_nums(
        run=datetime(2022, 11, 12, 0), forecast=1, parameter="DZDT", level="525 mb"
    )
    print(start_stop)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
