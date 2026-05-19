from src.acquisition.parser import RequestBuilder, ResponseParser
from src.core.exceptions import ParseError

def test_request_builder():
    url = RequestBuilder.build_seriescalc_url(36.0, 5.0, 2020, 2021)
    assert "lat=36.0" in url
    assert "lon=5.0" in url
    assert "startyear=2020" in url

def test_response_parser_missing_outputs():
    try:
        ResponseParser.parse({"bad": "data"}, 0, 0, 2020, 2021)
        assert False, "Should have raised ParseError"
    except ParseError:
        assert True
