from autoeval.loader import TestSuiteResult

class JSONReporter:
    def write(self, result: TestSuiteResult, output_path: str):
        """Serializes and writes the TestSuiteResult to a JSON file."""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result.model_dump_json(indent=2))
