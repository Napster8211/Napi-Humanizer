"""Flask application factory and web entry point for NapsterTec Text Intelligence Engine."""

import os
import logging
from flask import Flask, render_template, jsonify
from core.config import get_config, AppConfig
from api.routes import api_bp
from core.document_extractor import MAX_UPLOAD_BYTES


def create_app(config: AppConfig = None) -> Flask:
    """Create and configure the Flask web application."""
    cfg = config or get_config()

    # Configure logging
    log_level = getattr(logging, cfg.log_level, logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(base_dir, "ui", "templates")
    static_dir = os.path.join(base_dir, "ui", "static")

    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir,
    )
    app.config["ENGINE_CONFIG"] = cfg
    # JSON requests remain bounded by the configured text limit; uploads have a separate
    # bounded binary limit and are extracted transiently by /api/v1/extract.
    app.config["MAX_CONTENT_LENGTH"] = max((cfg.max_input_chars * 4) + 1024, MAX_UPLOAD_BYTES + (256 * 1024))

    # Register API blueprint
    app.register_blueprint(api_bp)

    @app.after_request
    def set_security_headers(response):
        """Inject robust security headers on every response."""
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self';"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response

    @app.route("/")
    def index():
        """Render workspace application."""
        return render_template(
            "index.html",
            app_env=cfg.app_env,
            llm_provider=cfg.llm_provider,
            max_input_chars=cfg.max_input_chars,
        )

    @app.route("/api/health")
    def health_alias():
        """Deployment-friendly health alias without exposing credentials."""
        return jsonify({
            "status": "healthy",
            "service": "NapsterTec Text Intelligence Engine",
            "version": "2.0.0",
            "config": cfg.safe_dict(),
        }), 200

    return app


# Application singleton
app = create_app()


def main():
    """Run local development server."""
    cfg = get_config()
    print(f"Starting NapsterTec Text Intelligence Engine on http://{cfg.host}:{cfg.port}")
    print(f"Provider: {cfg.llm_provider} (Model: {cfg.llm_model})")
    app.run(host=cfg.host, port=cfg.port, debug=cfg.debug)


if __name__ == "__main__":
    main()
