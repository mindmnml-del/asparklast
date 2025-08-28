"""
Import helper for components to access api_client
"""

import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import api_client
from api_client import api_client

__all__ = ['api_client']
