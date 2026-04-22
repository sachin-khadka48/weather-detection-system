from pathlib import Path
import os
import sys


SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from web_app import app, _read_port  # noqa: E402


if __name__ == '__main__':
    app.run(
        debug=os.getenv('FLASK_DEBUG', '1') == '1',
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=_read_port()
    )