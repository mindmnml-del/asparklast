#!/usr/bin/env python3
"""
Robust test runner for AISpark Studio
Handles environment setup and pytest execution
"""

import sys
import os
import subprocess
from pathlib import Path

def setup_environment():
    """Setup proper Python path and environment"""
    project_root = Path(__file__).parent.absolute()
    backend_path = project_root / "backend"
    
    # Add backend to Python path
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))
    
    # Set environment variables
    os.environ['PYTHONPATH'] = str(backend_path)
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    
    # Change to project root
    os.chdir(project_root)
    
    return project_root, backend_path

def run_tests(test_path=None, verbose=True):
    """Run pytest with proper configuration"""
    project_root, backend_path = setup_environment()
    
    # Default test path
    if test_path is None:
        test_path = "backend/tests/"
    
    # Pytest command
    cmd = [
        sys.executable, '-m', 'pytest',
        test_path,
        '-v' if verbose else '',
        '--tb=short',
        '--disable-warnings',
        '--no-header',
        '--rootdir=' + str(project_root)
    ]
    
    # Filter empty strings
    cmd = [arg for arg in cmd if arg]
    
    print(f"Running tests from: {project_root}")
    print(f"Test path: {test_path}")
    print(f"Backend path in PYTHONPATH: {backend_path}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        # Run tests
        result = subprocess.run(cmd, cwd=project_root, check=False)
        return result.returncode
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

def main():
    """Main entry point"""
    test_path = sys.argv[1] if len(sys.argv) > 1 else None
    exit_code = run_tests(test_path)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
