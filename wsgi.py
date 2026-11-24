"""Production WSGI entry point using Waitress."""

import sys
import logging
from web_ui import create_app
from core.config import get_config

logger = logging.getLogger("text_intelligence.wsgi")
app = create_app()

if __name__ == "__main__":
    cfg = get_config()
    try:
        from waitress import serve
        print(f"Serving NapsterTec Text Intelligence Engine with Waitress WSGI on http://{cfg.host}:{cfg.port}")
        serve(app, host=cfg.host, port=cfg.port, threads=4)
    except ImportError:
        print("Waitress not found. Falling back to WSGI development server.", file=sys.stderr)
        app.run(host=cfg.host, port=cfg.port, debug=False)
