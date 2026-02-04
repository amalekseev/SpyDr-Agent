# -*- coding: UTF-8 -*-
"""
Use behave4cmd0 step library (bundled w/ behave).
"""
import sys
from pathlib import Path

# -- ADD LOCAL BEHAVE TO PATH:
behave_path = Path(__file__).resolve().parents[2] / "behave"
sys.path.insert(0, str(behave_path))

# -- REGISTER STEPS FROM STEP-LIBRARY:
import behave4cmd0.__all_steps__  # noqa: F401
