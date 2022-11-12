"""Tests for grib.py."""
from openwx.grib import parse_grib_index


def test_parse_grib_index():
    """Tests that parse_grib_index creates properly formatted dictionaries."""
    idx = """1:0:d=2022111200:PRMSL:mean sea level:1 hour fcst:
2:990417:d=2022111200:CLWMR:1 hybrid level:1 hour fcst:
3:1068774:d=2022111200:ICMR:1 hybrid level:1 hour fcst:
4:1392291:d=2022111200:RWMR:1 hybrid level:1 hour fcst:
5:1637623:d=2022111200:SNMR:1 hybrid level:1 hour fcst:
6:1737623:d=2022111200:ICMR:surface:1 hour fcst:
"""

    actual = parse_grib_index(index=idx)
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
