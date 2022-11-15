"""Module for handling data retrieval from grib source data."""
import asyncio
import logging
from datetime import datetime
from tempfile import NamedTemporaryFile
from typing import Dict, List, Optional, Tuple

import aiohttp
import numpy as np
import xarray as xr
from xarray.core.types import InterpOptions

from openwx.gfs import GFSParameters
from openwx.models import Coords

BASE_URL = "https://noaa-gfs-bdp-pds.s3.amazonaws.com"
URL_PATTERN = "/gfs.{run_date}/{run_hour:02d}/atmos/gfs.t{run_hour:02d}z.pgrb2.0p25.f{forecast:03d}"


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


def get_param_levels_from_index(index: str) -> Dict[str, List[str]]:
    """Returns a dictionary of parameters and their available levels from idx data.

    Args:
        index (str): A string containing GRIB .idx data.

    Returns:
        Dict[str, List[str]]: Dictionary containing parameters with available levels.
    """
    parsed_index = parse_grib_index(index)
    result = {}
    for parameter, level_dicts in parsed_index.items():
        result[parameter] = [level_dict for level_dict in level_dicts]
    return result


def parse_grib_index(index: str) -> Dict[str, Dict[str, Dict[str, Optional[int]]]]:
    """Parses a grib index file into a usable dictionary.

    Args:
        index (str): The contents of the grib index file.

    Returns:
        Dict[str, Dict[str, Dict[str, Optional[int]]]]: A dictionary containing parameter, level,
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
) -> Tuple[Optional[int], Optional[int]]:
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
    if grib_index_key := GFSParameters.get_grib_index_key(parameter=parameter):

        param_dict = parsed_index.get(grib_index_key)
        if param_dict is not None:
            start_and_stop = param_dict.get(level)
            if start_and_stop is not None:
                start_byte = start_and_stop["start"]
                stop_byte = start_and_stop["stop"]
                return start_byte, stop_byte
            else:
                logging.warning("Level: %s is not in grib index.", level)
                return (None, None)
        else:
            logging.warning("Param: %s is not in grib index.", grib_index_key)
            return (None, None)
    else:
        logging.warning("Unable to find grib index key for param: %s", parameter)
        return (None, None)


async def get_grib_message(
    run: datetime, forecast: int, parameter: str, level: str
) -> Optional[bytes]:
    """Returns a raw GRIB message for the specified run, forecsst, parameter, and level.

    Args:
        run (datetime): Datetime of the model run.
        forecast (int): The forecast hour.
        parameter (str): The requested parameter.
        level (str): The requested level.

    Returns:
        Optional[bytes]: A raw GRIB message.
    """
    url = get_grib_url(run=run, forecast=forecast)
    bytes_start, bytes_stop = await get_start_stop_byte_nums(
        run=run, forecast=forecast, parameter=parameter, level=level
    )
    headers = {"Range": f"bytes={bytes_start}-{bytes_stop}"}
    if bytes_start is not None:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url=url) as response:
                grib_message = await response.read()
                assert grib_message[:4] == b"GRIB"
                return grib_message


def get_dataset_from_grib_message(grib_message: bytes) -> xr.Dataset:
    """Returns an xarray dataset from the provided grib message.

    Args:
        grib_message (bytes): A valid GRIB message.

    Returns:
        xr.Dataset: An xarray dataset.
    """
    with NamedTemporaryFile(mode="wb") as file:
        file.write(grib_message)
        return xr.open_dataset(file.name, engine="cfgrib")


async def get_parameter_value(
    run: datetime,
    forecast: int,
    parameter: str,
    level: str,
    coords: Coords,
    interp_method: InterpOptions = "linear",
) -> Optional[np.ndarray]:
    """Returns the value of a specific weather parameter at a provided location and time.

    Args:
        parameter (Parameter): The requested weather parameter.
        coords (Coords): The requested location.
        valid_time (datetime): The requested time.
        method (InterpOptions, optional): Method to use for Interpolation. Defaults to "linear".

    Returns:
        ArrayLike: The value of the requested weather parameter
    """
    grib_message = await get_grib_message(
        run=run, forecast=forecast, parameter=parameter, level=level
    )
    if grib_message is not None:
        with NamedTemporaryFile(mode="wb") as file:
            file.write(grib_message)
            ds = xr.open_dataset(file.name, engine="cfgrib")
            if grib_dataset_key := GFSParameters.get_grib_dataset_key(parameter):
                value = (
                    ds[
                        grib_dataset_key
                    ]  # TODO - Need to add translation from parameter to key
                    .interp(
                        latitude=coords.latitude,
                        longitude=coords.longitude,
                        method=interp_method,
                    )
                    .data
                )

                return value


async def main():
    """Main function used for easier testing in development."""
    # run = datetime(2022, 11, 12, 0)
    # forecast = 1
    # parameter = "TMP"
    # level = "2 m above ground"

    # parsed_index = parse_grib_index(
    # await get_grib_index(run=run, forecast=forecast)
    # )
    # print(parsed_index)
    # params = get_param_levels_from_index(
    # await get_grib_index(run=run, forecast=forecast)
    # )
    # print(params.get(parameter))
    # start_stop = await get_start_stop_byte_nums(
    # run=run, forecast=forecast, parameter=parameter, level=level
    # )
    # print(start_stop)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
