import sys
from pathlib import Path

# Make project root importable (main, core, mcp_client).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
