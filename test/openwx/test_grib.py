"""Tests for grib.py."""
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from openwx.grib import (
    get_grib_idx_url,
    get_grib_index,
    get_grib_url,
    get_start_stop_byte_nums,
    parse_grib_index,
)


@pytest.fixture
def mocked_idx_data():
    """Provides a mocked idx file fixture."""
    return """1:0:d=2022111200:PRMSL:mean sea level:1 hour fcst:
2:990417:d=2022111200:CLWMR:1 hybrid level:1 hour fcst:
3:1068774:d=2022111200:ICMR:1 hybrid level:1 hour fcst:
4:1392291:d=2022111200:RWMR:1 hybrid level:1 hour fcst:
5:1637623:d=2022111200:SNMR:1 hybrid level:1 hour fcst:
6:1737623:d=2022111200:ICMR:surface:1 hour fcst:
"""


def test_parse_grib_index(mocked_idx_data):
    """Tests that parse_grib_index creates properly formatted dictionaries."""
    actual = parse_grib_index(index=mocked_idx_data)
    expected = {
        "PRMSL": {"mean sea level": {"start": 0, "stop": 990416}},
        "CLWMR": {"1 hybrid level": {"start": 990417, "stop": 1068773}},
        "ICMR": {
            "1 hybrid level": {"start": 1068774, "stop": 1392290},
            "surface": {"start": 1737623, "stop": None},
        },
        "RWMR": {"1 hybrid level": {"start": 1392291, "stop": 1637622}},
        "SNMR": {"1 hybrid level": {"start": 1637623, "stop": 1737622}},
    }
    assert actual == expected


@pytest.mark.asyncio
@patch("openwx.grib.aiohttp.ClientSession.get")
async def test_get_grib_index(mocked_get: AsyncMock) -> None:
    """Tests that get_grib_index calls the correct URLs.

    Args:
        mocked_get (AsyncMock): A mocked ClientSession.get object.

    Returns:
        None
    """
    mocked_return = "some mocked text"
    mocked_get.return_value.__aenter__.return_value.text.return_value = mocked_return
    actual = await get_grib_index(run=datetime(2022, 11, 12, 0), forecast=1)
    assert actual == mocked_return
    mocked_get.assert_called_with(
        "https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.20221112/00/atmos/gfs.t00z.pgrb2b.0p25.f001.idx"
    )


def test_get_grib_url() -> None:
    """Tests get_grib_url returns a correctly formatted URL."""
    expected = "https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.20221112/00/atmos/gfs.t00z.pgrb2b.0p25.f001"
    actual = get_grib_url(run=datetime(2022, 11, 12, 0), forecast=1)
    assert actual == expected


def test_get_grib_idx_url() -> None:
    """Tests get_grib_idx_url returns a correctly formatted URL."""
    expected = "https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.20221112/00/atmos/gfs.t00z.pgrb2b.0p25.f001.idx"
    actual = get_grib_idx_url(run=datetime(2022, 11, 12, 0), forecast=1)
    assert actual == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "parameter, level, expected_result",
    [
        ("PRMSL", "mean sea level", (0, 990416)),
        ("CLWMR", "1 hybrid level", (990417, 1068773)),
        ("ICMR", "surface", (1737623, None)),
        ("BOOP", "surface", None),
    ],
)
@patch("openwx.grib.get_grib_index")
async def test_get_start_stop_byte_nums(
    mocked_get_grib_index,
    parameter,
    level,
    expected_result,
    mocked_idx_data,
) -> None:
    """Tests get_start_and_stop_byte_nums returns the correct values."""
    mocked_get_grib_index.return_value = mocked_idx_data
    actual = await get_start_stop_byte_nums(
        run=datetime(2022, 11, 12, 0), forecast=1, parameter=parameter, level=level
    )
    assert actual == expected_result
