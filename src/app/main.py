"""Main module for FastAPI app."""
from dataclasses import asdict
from datetime import datetime

from fastapi import Depends, FastAPI, Query

from openwx import gfs
from openwx.gfs import ParameterName, get_hours_from_range, get_parameter_value
from openwx.models import Coords, Forecast, ForecastResponseModel

app = FastAPI()


@app.get("/")
async def root() -> dict[str, str]:
    """Defines root endpoint.

    Returns:
        dict[str, str]: Hard Coded: {"message": "Hello World"}_
    """
    return {"message": "Hello World"}


@app.get("/parameterInfo")
async def parameter_info() -> list[dict[str, str]]:
    """Returns a list of available parameters and their associated metadata.

    Returns:
        list[dict[str, str]]: A list of available parameters and their associated metadata.
    """
    response = []
    for param, metadata in gfs.PARAMETERS.items():
        response.append(
            {"parameter": param.value, "parameter_metadata": asdict(metadata)}
        )

    return response


@app.get("/queryParameters", response_model=ForecastResponseModel)
async def param(
    model_run: datetime,
    valid_time_start: datetime,
    valid_time_end: datetime,
    coords: Coords = Depends(),
    parameters: list[str] = Query(enum=[item for item in ParameterName]),
) -> ForecastResponseModel:
    """Provides endpoint to allow users to query model parameter data.

    Args:
        model_run (datetime): A datetime object for the requested model run.
        valid_time_start (datetime): The starting valid time for the request.
        valid_time_end (datetime): The ending valid time for the request.
        coords (Coords, optional): The coordinates for the request. Defaults to Depends().
        parameters (list[str], optional): The requested parameters. Defaults to Query(enum=[item for item in ParameterName]).

    Returns:
        ForecastResponseModel: The response model for the selected parameter data.
    """
    response_forecasts = []
    response_parameters = {}
    valid_times = get_hours_from_range(
        start_time=valid_time_start, end_time=valid_time_end
    )
    for valid_time in valid_times:
        for parameter in parameters:
            param_value = get_parameter_value(
                coords=coords,
                parameter=parameter,
                valid_time=valid_time,
                model_run=model_run,
            )
            response_parameters[parameter] = param_value.tolist()

        response_forecasts.append(
            Forecast(valid_time=valid_time, parameters=response_parameters)
        )

    response = ForecastResponseModel(
        lat=coords.latitude, lon=coords.longitude, forecasts=response_forecasts
    )

    return response
