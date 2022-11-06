"""Initial test script used in development."""
import datetime as dt
from dataclasses import dataclass
from datetime import datetime

import xarray as xr
from numpy.typing import ArrayLike
from xarray.core.types import InterpOptions


@dataclass
class Location:
    """Dataclass used to store a Location."""

    name: str
    latitude: float
    longitude: float


@dataclass
class Parameter:
    """Dataclass used to store weather parameter info."""

    name: str
    key: str


desired_locations = [Location(name="Home", latitude=41.09, longitude=180 - 95.94)]

desired_params = [
    Parameter(name="temperature", key="tmp2m"),
    Parameter(name="relative humidity", key="rh2m"),
    Parameter(name="wind speed (gust)", key="gustsfc"),
]


def get_parameter_value(
    parameter: Parameter,
    location: Location,
    valid_time: datetime,
    method: InterpOptions = "linear",
) -> ArrayLike:
    """Returns the value of a specific weather parameter at a provided location and time.

    Args:
        parameter (Parameter): The requested weather parameter.
        location (Location): The requested location.
        valid_time (datetime): The requested time.
        method (InterpOptions, optional): Method to use for Interpolation. Defaults to "linear".

    Returns:
        ArrayLike: The value of the requested weather parameter
    """
    gfs_link = "http://nomads.ncep.noaa.gov:80/dods/gfs_0p25/gfs20221105/gfs_0p25_12z"
    ds = xr.open_dataset(gfs_link, use_cftime=True)

    value = (
        ds[parameter.key]
        .sel(time=valid_time)
        .interp(lat=location.latitude, lon=location.longitude, method=method)
        .data
    )

    return value


def main() -> None:
    """Main function used for testing."""
    for location in desired_locations:
        time = dt.datetime(2022, 11, 5, 12)
        print(f"{location.name}: {time.isoformat()}")
        for parameter in desired_params:
            print(
                f"{parameter.name}: {get_parameter_value(parameter=parameter, location=location, valid_time=time)}"
            )


if __name__ == "__main__":
    main()
