"""Main module for FastAPI app."""
from datetime import datetime

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Query

from openwx import grib
from openwx.gfs import GFSParameters, get_hours_from_range, get_parameter_value
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
    for parameter in GFSParameters.parameters():
        response.append(
            {"parameter": parameter.short_name, "unit": parameter.model_unit}
        )

    return response


@app.get("/queryParameters", response_model=ForecastResponseModel)
async def query_parameters(
    model_run: datetime,
    valid_time_start: datetime,
    valid_time_end: datetime,
    coords: Coords = Depends(),
    parameters: list[str] = Query(alias="parameter"),
) -> ForecastResponseModel:
    """Provides endpoint to allow users to query model parameter data.

    Args:
        model_run (datetime): A datetime object for the requested model run.
        valid_time_start (datetime): The starting valid time for the request.
        valid_time_end (datetime): The ending valid time for the request.
        coords (Coords, optional): The coordinates for the request.
        parameters (list[str], optional): The requested parameters.

    Returns:
        ForecastResponseModel: The response model for the selected parameter data.
    """
    valid_parameters = list(GFSParameters.parameter_names())
    invalid_params = [param for param in parameters if param not in valid_parameters]
    if len(invalid_params) > 0:
        raise HTTPException(
            status_code=400,
            detail=f"The following parameter entries were invalid: {invalid_params}",
        )
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


@app.get("/queryGribParameters", response_model=ForecastResponseModel)
async def query_grib_parameters(
    run: datetime,
    valid_time_start: datetime,
    valid_time_end: datetime,
    coords: Coords = Depends(),
    parameters: list[str] = Query(alias="parameter"),
) -> ForecastResponseModel:
    """Provides endpoint to allow users to query model parameter data.

    Args:
        model_run (datetime): A datetime object for the requested model run.
        valid_time_start (datetime): The starting valid time for the request.
        valid_time_end (datetime): The ending valid time for the request.
        coords (Coords, optional): The coordinates for the request.
        parameters (list[str], optional): The requested parameters.

    Returns:
        ForecastResponseModel: The response model for the selected parameter data.
    """
    valid_parameters = list(GFSParameters.parameter_names())
    invalid_params = [param for param in parameters if param not in valid_parameters]
    if len(invalid_params) > 0:
        raise HTTPException(
            status_code=400,
            detail=f"The following parameter entries were invalid: {invalid_params}",
        )
    response_forecasts = []
    response_parameters = {}
    valid_times = get_hours_from_range(
        start_time=valid_time_start, end_time=valid_time_end
    )
    for valid_time in valid_times:
        forecast = (valid_time - run).seconds // 3600
        for parameter in parameters:
            if grib_param := GFSParameters.from_string(parameter):
                param_value = grib.get_parameter_value(
                    run=run,
                    coords=coords,
                    level="2 m above ground",
                    parameter=grib_param.grib_index_key,
                    forecast=forecast,
                )
                response_parameters[parameter] = await param_value

        print(valid_time, response_parameters)
        response_forecasts.append(
            Forecast(valid_time=valid_time, parameters=response_parameters)
        )

    response = ForecastResponseModel(
        lat=coords.latitude, lon=coords.longitude, forecasts=response_forecasts
    )

    return response


if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, log_level="info", reload=True)
