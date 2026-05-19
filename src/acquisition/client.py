import requests
from src.acquisition.parser import RequestBuilder, ResponseParser
from src.core.datatypes import PvgisYearBounds
from src.core.exceptions import NetworkError, TimeoutError, HTTPError, CoverageError, ParseError


class PVGISClient:
    def __init__(self):
        self.timeout_sec = 30
        self.session = requests.Session()

    def fetch_year_bounds(self, lat: float, lon: float) -> PvgisYearBounds:
        """Query PVGIS for the radiation DB and year range valid at this location."""
        url = RequestBuilder.build_mrcalc_url(lat, lon)
        data = self._execute_get(url)
        return ResponseParser.parse_year_bounds(data)

    def fetch_irradiance(
        self, lat: float, lon: float, start_year: int, end_year: int,
        loss_pct: float = 14.0,
    ):
        url = RequestBuilder.build_seriescalc_url(
            lat, lon, start_year, end_year, loss_pct=loss_pct,
        )
        data = self._execute_get(url)
        return ResponseParser.parse(data, lat, lon, start_year, end_year)

    def _execute_get(self, url: str) -> dict:
        try:
            response = self.session.get(url, timeout=self.timeout_sec)

            if response.status_code == 400:
                # Read the response body to discriminate: coverage error vs bad request
                try:
                    body = response.json()
                    message = body.get("message", "").lower()
                except Exception:
                    message = response.text.lower()

                if "location" in message or "coverage" in message or "outside" in message:
                    raise CoverageError("Coordinates are outside the PVGIS coverage area.")
                else:
                    raise HTTPError(
                        f"PVGIS rejected the request (HTTP 400). "
                        f"Details: {response.text[:200]}"
                    )

            response.raise_for_status()
            return response.json()

        except (CoverageError, HTTPError):
            raise  # Re-raise our own typed exceptions untouched

        except requests.exceptions.Timeout:
            raise TimeoutError("Connection to PVGIS timed out after 30 seconds.")

        except requests.exceptions.ConnectionError:
            raise NetworkError("Could not reach the PVGIS server. Check your internet connection.")

        except requests.exceptions.HTTPError as e:
            raise HTTPError(f"HTTP Error from PVGIS: {str(e)}")

        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Network Error: {str(e)}")