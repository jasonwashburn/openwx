"""The module response for configuration and querying of GFS data."""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Generator, Iterable, Optional

import numpy as np
import xarray as xr
from xarray.core.types import InterpOptions

from openwx.models import Coords


@dataclass
class ParameterMetadata:
    """A dataclass for storing parameter metadata."""

    short_name: str
    nc_dataset_key: str
    grib_index_key: str
    grib_dataset_key: str
    model_unit: str


@dataclass
class GFSParameters:
    """An enum for common weather parameters."""

    temperature_2m: ParameterMetadata = ParameterMetadata(
        short_name="temperature_2m",
        nc_dataset_key="tmp2m",
        grib_index_key="TMP",
        grib_dataset_key="t2m",
        model_unit="k",
    )
    relative_humidty_2m: ParameterMetadata = ParameterMetadata(
        short_name="relative_humidity_2m",
        nc_dataset_key="rh2m",
        grib_index_key="RH",
        grib_dataset_key="r2",
        model_unit="%",
    )
    gust_surface: ParameterMetadata = ParameterMetadata(
        short_name="gust_surface",
        nc_dataset_key="gustsfc",
        grib_index_key="GUST",
        grib_dataset_key="gust",
        model_unit="m/s",
    )

    @classmethod
    def from_string(cls, parameter_name: str) -> Optional[ParameterMetadata]:
        """Returns the ParameterMetadata object for the requested parameter.

        Args:
            parameter_name (str): The short name of the desired parameter.

        Returns:
            Optional[ParameterMetadata]: The matching ParameterData object, otherwise None.
        """
        for parameter in cls.parameters():
            if parameter_name == parameter.short_name:
                return parameter
        else:
            return None

    @classmethod
    def parameter_names(cls) -> Generator[str, None, None]:
        """Returns a generator of parameter short names.

        Yields:
            Generator[str, None, None]: A generator of parameter short names.
        """
        for parameter in cls.parameters():
            yield parameter.short_name

    @classmethod
    def parameters(cls) -> Generator[ParameterMetadata, None, None]:
        """Returns a Generator of parameter names.

        Yields:
            Generator[str, None, None]: A genrator of parameter names.
        """
        for attr in vars(cls).values():
            if isinstance(attr, ParameterMetadata):
                yield attr

    @classmethod
    def get_grib_index_key(cls, parameter: str) -> Optional[str]:
        """Returns a grib index key for the requested parameter.

        Args:
            parameter (str): The requested parameter.

        Returns:
            Optional[str]: The GRIB index key for the requested param if it exists.
        """
        if parameter_metadata := cls.from_string(parameter):
            return parameter_metadata.grib_index_key
        else:
            return None

    @classmethod
    def get_grib_dataset_key(cls, parameter: str) -> Optional[str]:
        """Returns the grib dataset key for the requested parameter.

        Args:
            parameter (str): The requested parameter.

        Returns:
            Optional[str]: The xarray dataset key for the requested parameter.
        """
        if parameter_metadata := cls.from_string(parameter):
            return parameter_metadata.grib_dataset_key
        else:
            return None


def get_nc_dataset_key(parameter: str) -> Optional[str]:
    """Returns the model key used to retrieve the requested parameter.

    Args:
        parameter (ParameterName): The requested parameter.

    Returns:
        Optional[str]: The model key of the requested parameter, otherwise None
    """
    if param_data := GFSParameters.from_string(parameter_name=parameter):
        return param_data.nc_dataset_key
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

    param_key = get_nc_dataset_key(parameter=parameter)

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
