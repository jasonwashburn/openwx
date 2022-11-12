"""The module response for configuration and querying of GFS data."""
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Iterable, Optional

import numpy as np
import xarray as xr
from xarray.core.types import InterpOptions

from openwx.models import Coords


class ParameterName(Enum):
    """An enum for common weather parameters."""

    TEMPERATURE = "temperature"
    RELHUMIDITY = "relative_humidity"
    GUST_SPEED = "wind_gust_speed"


@dataclass
class ParameterMetadata:
    """A dataclass for storing parameter metadata."""

    model_key: str
    model_unit: str


PARAMETERS = {
    ParameterName.TEMPERATURE: ParameterMetadata(model_key="tmp2m", model_unit="k"),
    ParameterName.RELHUMIDITY: ParameterMetadata(model_key="rh2m", model_unit="%"),
    ParameterName.GUST_SPEED: ParameterMetadata(model_key="gustsfc", model_unit="m/s"),
}


def get_model_key(parameter: str) -> Optional[str]:
    """Returns the model key used to retrieve the requested parameter.

    Args:
        parameter (ParameterName): The requested parameter.

    Returns:
        Optional[str]: The model key of the requested parameter, otherwise None
    """
    parameter_enum = ParameterName(parameter)
    parameter_metadata = PARAMETERS.get(parameter_enum)
    if parameter_metadata is not None:
        return parameter_metadata.model_key
    else:
        return None


def get_hours_from_range(
    start_time: datetime, end_time: datetime, interval: int = 1
) -> Iterable[datetime]:
    """Generates datetimes for each hour at the requested interval between two dates.

    Args:
        start_time (datetime): The start date and time.
        end_time (datetime): The end date and time.
        interval (int, optional): The number of hours between each interval. Defaults to 1.

    Returns:
        Iterable[datetime]: An itterable of datetime objects at the requested interval.

    Yields:
        Iterator[Iterable[datetime]]: Datetime objects at the requested interval.
    """
    increment_time = start_time
    while increment_time <= end_time:
        yield increment_time
        increment_time += timedelta(hours=interval)


def get_parameter_value(
    parameter: str,
    coords: Coords,
    valid_time: datetime,
    model_run: datetime,
    interp_method: InterpOptions = "linear",
    selection_method: str = "nearest",
) -> np.ndarray:
    """Returns the value of a specific weather parameter at a provided location and time.

    Args:
        parameter (Parameter): The requested weather parameter.
        coords (Coords): The requested location.
        valid_time (datetime): The requested time.
        method (InterpOptions, optional): Method to use for Interpolation. Defaults to "linear".

    Returns:
        ArrayLike: The value of the requested weather parameter
    """
    model_date = model_run.strftime("%Y%m%d")
    model_hour = model_run.strftime("%H")
    base_url = "http://nomads.ncep.noaa.gov:80"
    gfs_link = (
        f"{base_url}/dods/gfs_0p25_1hr/gfs{model_date}/gfs_0p25_1hr_{model_hour}z"
    )
    ds = xr.open_dataset(gfs_link, use_cftime=True)

    param_key = get_model_key(parameter=parameter)

    value = (
        ds[param_key]
        .sel(time=valid_time, method=selection_method)
        .interp(lat=coords.latitude, lon=coords.longitude, method=interp_method)
        .data
    )

    return value


def main() -> None:
    """Main function."""
    pass


if __name__ == "__main__":
    main()
