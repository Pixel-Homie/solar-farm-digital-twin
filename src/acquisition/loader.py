import csv
import os

from src.core.exceptions import ParseError
from src.core.paths import data_path


class CatalogLoader:
    def __init__(self, file_path: str | None = None):
        self.file_path = file_path or data_path("components.csv")

    def load_catalogue(self):
        panels = []
        batteries =[]
        if not os.path.exists(self.file_path):
            return panels, batteries

        try:
            with open(self.file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    parsed = self._parse_row(row)
                    if parsed['type'] == 'PANEL':
                        panels.append(parsed)
                    elif parsed['type'] == 'BATTERY':
                        batteries.append(parsed)
            return panels, batteries
        except Exception as e:
            raise ParseError(f"Failed to parse catalogue CSV: {str(e)}")

    def _parse_row(self, row: dict) -> dict:
        return {
            'component_id': row['component_id'],
            'type': row['type'],
            'name': row['name'],
            'rated_power_w': float(row['rated_power_w']),
            'efficiency': float(row['efficiency']),
            'capacity_wh': float(row['capacity_wh'])
        }
