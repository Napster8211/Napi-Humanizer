"""REST API routes and request handlers."""

import time
from typing import Dict, Any, List
from flask import Blueprint, request, jsonify, current_app
from pydantic import ValidationError as PydanticValidationError

from core.schemas import RewriteRequest, AnalysisRequest
from core.orchestrator import get_orchestrator
from core.analyzer import get_analyzer
from core.errors import (
    TextIntelligenceError,
    ValidationError,
    EmptyInputError,
    InputTooLargeError,
    ProviderMissingKeyError,
    ProviderTimeoutError,
    ProviderRateLimitError,
    ProviderError,
)
from editing.modes import MODE_METADATA, INTENSITY_METADATA

api_bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")

# Simple in-memory sliding rate limiter per client IP
_rate_limit_cache: Dict[str, List[float]] = {}


def check_rate_limit(client_ip: str, limit_per_minute: int) -> bool:
    """Return True if request is allowed, False if limit is exceeded."""
    now = time.time()
    window_start = now - 60.0

    timestamps = _rate_limit_cache.get(client_ip, [])
    # Filter timestamps older than 60 seconds
    timestamps = [t for t in timestamps if t > window_start]

    if len(timestamps) >= limit_per_minute:
        _rate_limit_cache[client_ip] = timestamps
        return False

    timestamps.append(now)
    _rate_limit_cache[client_ip] = timestamps
    return True


@api_bp.before_request
def enforce_rate_limiting():
    """Apply rate limiting to API endpoints."""
    config = current_app.config.get("ENGINE_CONFIG")
    limit = config.rate_limit_per_minute if config else 60
    client_ip = request.remote_addr or "unknown"

    if not check_rate_limit(client_ip, limit):
        return jsonify({
            "error": "RateLimitExceeded",
            "message": f"Rate limit of {limit} requests per minute exceeded. Please wait before retrying.",
        }), 429


@api_bp.route("/rewrite", methods=["POST"])
def rewrite_text():
    """Execute text refinement request."""
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "InvalidJSON", "message": "Request body must be valid JSON."}), 400

    try:
        req = RewriteRequest(**data)
        orchestrator = get_orchestrator()
        result = orchestrator.rewrite(req)
        return jsonify(result.model_dump()), 200

    except EmptyInputError as exc:
        return jsonify({"error": "EmptyInput", "message": str(exc)}), 400
    except InputTooLargeError as exc:
        return jsonify({"error": "InputTooLarge", "message": str(exc)}), 413
    except PydanticValidationError as exc:
        errors = [
            {"field": ".".join(str(loc) for loc in err.get("loc", [])), "message": err.get("msg", "Invalid value")}
            for err in exc.errors()
        ]
        return jsonify({"error": "ValidationError", "details": errors}), 400
    except ValidationError as exc:
        return jsonify({"error": "ValidationError", "message": str(exc)}), 400
    except ProviderMissingKeyError as exc:
        return jsonify({"error": "ProviderMissingKey", "message": str(exc)}), 503
    except ProviderRateLimitError as exc:
        return jsonify({"error": "ProviderRateLimit", "message": str(exc)}), 429
    except ProviderTimeoutError as exc:
        return jsonify({"error": "ProviderTimeout", "message": str(exc)}), 504
    except ProviderError as exc:
        return jsonify({"error": "ProviderError", "message": str(exc)}), 502
    except Exception as exc:
        current_app.logger.exception("Unexpected error during text rewrite.")
        return jsonify({"error": "InternalError", "message": "An unexpected error occurred."}), 500


@api_bp.route("/rewrite/stream", methods=["POST"])
def rewrite_text_stream():
    """Execute text refinement request with Server-Sent Events (SSE) streaming."""
    from flask import Response, stream_with_context

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "InvalidJSON", "message": "Request body must be valid JSON."}), 400

    try:
        req = RewriteRequest(**data)
        orchestrator = get_orchestrator()
        generator = orchestrator.rewrite_stream(req)
        response = Response(stream_with_context(generator), mimetype="text/event-stream")
        response.headers["Cache-Control"] = "no-cache"
        response.headers["X-Accel-Buffering"] = "no"
        return response

    except EmptyInputError as exc:
        return jsonify({"error": "EmptyInput", "message": str(exc)}), 400
    except InputTooLargeError as exc:
        return jsonify({"error": "InputTooLarge", "message": str(exc)}), 413
    except PydanticValidationError as exc:
        errors = [
            {"field": ".".join(str(loc) for loc in err.get("loc", [])), "message": err.get("msg", "Invalid value")}
            for err in exc.errors()
        ]
        return jsonify({"error": "ValidationError", "details": errors}), 400
    except Exception as exc:
        current_app.logger.exception("Unexpected error initializing streaming rewrite.")
        return jsonify({"error": "InternalError", "message": "An unexpected error occurred."}), 500


@api_bp.route("/analyze", methods=["POST"])
def analyze_text():
    """Analyze text metrics and protected spans without rewriting."""
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "InvalidJSON", "message": "Request body must be valid JSON."}), 400

    try:
        req = AnalysisRequest(**data)
        analyzer = get_analyzer()
        result = analyzer.analyze(req.text)
        return jsonify(result.model_dump()), 200

    except PydanticValidationError as exc:
        errors = [
            {"field": ".".join(str(loc) for loc in err.get("loc", [])), "message": err.get("msg", "Invalid value")}
            for err in exc.errors()
        ]
        return jsonify({"error": "ValidationError", "details": errors}), 400
    except Exception as exc:
        current_app.logger.exception("Unexpected error during text analysis.")
        return jsonify({"error": "InternalError", "message": "An unexpected error occurred."}), 500


@api_bp.route("/modes", methods=["GET"])
def list_modes():
    """List available editing modes and intensities."""
    modes = [
        {
            "id": mode.value,
            "title": meta["title"],
            "description": meta["description"],
        }
        for mode, meta in MODE_METADATA.items()
    ]
    intensities = [
        {
            "id": intensity.value,
            "title": meta["title"],
            "guidance": meta["guidance"],
        }
        for intensity, meta in INTENSITY_METADATA.items()
    ]
    return jsonify({
        "modes": modes,
        "intensities": intensities,
    }), 200


@api_bp.route("/health", methods=["GET"])
def health_check():
    """System health check and non-sensitive configuration diagnostics."""
    config = current_app.config.get("ENGINE_CONFIG")
    safe_info = config.safe_dict() if config else {}
    return jsonify({
        "status": "healthy",
        "service": "NapsterTec Text Intelligence Engine",
        "version": "2.0.0",
        "config": safe_info,
    }), 200
