from src.core.datatypes import IrradianceData, PvgisYearBounds
from src.core.exceptions import ParseError


class RequestBuilder:
    _API_BASE = "https://re.jrc.ec.europa.eu/api/v5_3"

    @staticmethod
    def build_mrcalc_url(lat: float, lon: float) -> str:
        """Lightweight call — response includes per-location year_min/year_max."""
        return (
            f"{RequestBuilder._API_BASE}/MRcalc"
            f"?lat={lat}&lon={lon}&outputformat=json"
        )

    @staticmethod
    def build_seriescalc_url(
        lat: float, lon: float, start_year: int, end_year: int,
        loss_pct: float = 14.0,
    ) -> str:
        base_url = f"{RequestBuilder._API_BASE}/seriescalc"
        loss = max(0, min(30, int(round(loss_pct))))
        params = (
            f"lat={lat}"
            f"&lon={lon}"
            f"&startyear={start_year}"
            f"&endyear={end_year}"
            f"&outputformat=json"
            f"&pvcalculation=1"
            f"&peakpower=1"
            f"&loss={loss}"
        )
        return f"{base_url}?{params}"


class ResponseParser:
    @staticmethod
    def parse_year_bounds(payload: dict) -> PvgisYearBounds:
        try:
            meteo = payload["inputs"]["meteo_data"]
            return PvgisYearBounds(
                year_min=int(meteo["year_min"]),
                year_max=int(meteo["year_max"]),
                radiation_db=str(meteo["radiation_db"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ParseError(
                "Could not read PVGIS year limits from API response."
            ) from exc

    @staticmethod
    def parse(payload: dict, lat: float, lon: float, start_year: int, end_year: int) -> IrradianceData:
        if "outputs" not in payload or "hourly" not in payload["outputs"]:
            raise ParseError("Malformed API response: 'outputs.hourly' missing.")

        hourly_list = payload["outputs"]["hourly"]
        parsed_data = []

        for item in hourly_list:
            if "time" not in item or "G(i)" not in item:
                continue

            ts = str(item["time"])
            irr = float(item["G(i)"])
            temp = float(item.get("T2m", 25.0))

            parsed_data.append({
                "timestamp": ts,
                "irradiance_wm2": irr,
                "temperature_c": temp
            })

        return IrradianceData(
            lat=lat,
            lon=lon,
            start_year=start_year,
            end_year=end_year,
            hourly_values=parsed_data
        )