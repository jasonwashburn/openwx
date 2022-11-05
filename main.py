"""Initial test script used in development."""

import datetime as dt

import xarray as xr

desired_locations = [{"name": "Home", "lat": 41.09, "lon": -95.94}]

desired_params = [{"key": "tmp2m"}, {"key": "rh2m"}, {"key": "gustsfc"}]


def main() -> None:
    """Main function used for testing."""
    gfs_link = "http://nomads.ncep.noaa.gov:80/dods/gfs_0p25/gfs20221105/gfs_0p25_12z"

    ds = xr.open_dataset(gfs_link)

    for location in desired_locations:
        lat = location.get("lat")
        lon = location.get("lon")
        time = dt.datetime.utcnow()
        for param in desired_params:
            print(
                f"{param}: ",
                ds[param.get("key")]
                .sel(lat=lat, lon=lon, time=time, method="nearest")
                .data,
            )


if __name__ == "__main__":
    main()
