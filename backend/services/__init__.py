"""
AISpark Studio Backend Package
Optimized and consolidated architecture
"""

# Ensure the backend package path is available when running tests/tools from repo root
import sys
from pathlib import Path
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
	sys.path.insert(0, str(backend_dir))

__version__ = "2.0.0"
__author__ = "AISpark Studio Team"
