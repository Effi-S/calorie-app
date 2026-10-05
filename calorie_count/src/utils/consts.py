"""Here we store Constants (mostly to avoid 'magic numbers' )"""

from pathlib import Path

MAIN_KV = str((Path(__file__).parent.parent / "kv_files" / "main.kv").resolve())
