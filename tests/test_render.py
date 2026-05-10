"""
Test the HTML newspaper dashboard using sample data — no API calls, no quota used.
Run: python test_render.py
"""

import os
import webbrowser
from pathlib import Path

from tests.sample_data import SAMPLE_TOPICS
from dashboard.render import render

if __name__ == "__main__":
    print("Rendering test dashboard...")
    output_path = render(SAMPLE_TOPICS, output_dir="output")
    abs_path = Path(output_path).resolve()
    print(f"Done: {abs_path}")
    webbrowser.open(abs_path.as_uri())
