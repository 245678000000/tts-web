from __future__ import annotations

import os
import sys

# Ensure project root is importable in Vercel serverless runtime.
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from web_app import app

