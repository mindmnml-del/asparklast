"""Frontend components package"""

import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
