"""
Medium complexity data processing with common patterns
"""

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class DataProcessor:
    """Process various data formats with validation"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.processed_count = 0
        self.error_count = 0

    def process_json_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Process JSON file with error handling"""
        try:
            with open(file_path) as f:
                data = json.load(f)
            self.processed_count += 1
            return self._validate_data(data)
        except FileNotFoundError:
            self.error_count += 1
            return None
        except json.JSONDecodeError:
            self.error_count += 1
            return None

    def process_csv_file(self, file_path: str) -> List[Dict[str, str]]:
        """Process CSV file with error handling"""
        results = []
        try:
            with open(file_path) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    validated_row = self._validate_row(row)
                    if validated_row:
                        results.append(validated_row)
            self.processed_count += 1
        except FileNotFoundError:
            self.error_count += 1
        except Exception:
            self.error_count += 1
        return results

    def _validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data structure"""
        required_fields = self.config.get("required_fields", [])
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        return data

    def _validate_row(self, row: Dict[str, str]) -> Optional[Dict[str, str]]:
        """Validate CSV row"""
        if not row:
            return None

        # Remove empty values
        cleaned_row = {k: v for k, v in row.items() if v.strip()}

        # Check minimum fields
        min_fields = self.config.get("min_fields", 1)
        if len(cleaned_row) < min_fields:
            return None

        return cleaned_row

    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            "processed": self.processed_count,
            "errors": self.error_count,
            "success_rate": self.processed_count / (self.processed_count + self.error_count)
            if (self.processed_count + self.error_count) > 0
            else 0,
        }


def batch_process_files(file_paths: List[str], config: Dict[str, Any]) -> Dict[str, Any]:
    """Batch process multiple files"""
    processor = DataProcessor(config)
    results = []

    for file_path in file_paths:
        path = Path(file_path)
        if path.suffix == ".json":
            result = processor.process_json_file(file_path)
            if result:
                results.append(result)
        elif path.suffix == ".csv":
            result = processor.process_csv_file(file_path)
            results.extend(result)

    return {"results": results, "stats": processor.get_stats()}
