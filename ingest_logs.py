"""
ingest_logs.py
Parses chat export files (GPT, Claude, Grok) into structured entries
for inclusion in docs/03-Sessions-Index.md
"""

from pathlib import Path
import re
import json
from datetime import datetime

class SessionIngestor:
    def __init__(self, source_dir="sessions", output_file="docs/03-Sessions-Index.md"):
        self.source_dir = Path(source_dir)
        self.output_file = Path(output_file)
        self.entries = []

    def parse_file(self, path: Path):
        text = path.read_text(encoding="utf-8", errors="ignore")
        # Simple metadata grab: date + model name
        date_match = re.search(r"\d{4}-\d{2}-\d{2}", text)
        model_match = re.search(r"(GPT|Claude|Grok)", text, re.I)
        date = date_match.group(0) if date_match else "Unknown"
        model = model_match.group(0).upper() if model_match else "UNKNOWN"
        self.entries.append({
            "file": path.name,
            "model": model,
            "date": date,
            "lines": len(text.splitlines()),
        })

    def run(self):
        for file in sorted(self.source_dir.glob("*.docx")):
            self.parse_file(file)
        self.write_index()

    def write_index(self):
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_file, "w", encoding="utf-8") as f:
            f.write("# Sessions Index\n\n")
            for e in self.entries:
                f.write(f"- **{e['file']}** — {e['model']} — {e['date']} — {e['lines']} lines\n")

if __name__ == "__main__":
    ingestor = SessionIngestor()
    ingestor.run()
    print(f"Ingested {len(ingestor.entries)} sessions.")
