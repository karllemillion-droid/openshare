import logging
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

def init_limiter(app: Flask):
    limiter.init_app(app)

    # Log chaque tentative bloquée
    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        ip = get_remote_address()
        logging.warning(f"Rate limit dépassé — IP: {ip} — Route: {request.path}")
        return jsonify(error="Trop de requêtes. Réessayez plus tard."), 429


def setup_logging(app: Flask):
    """Configure les logs de sécurité dans un fichier dédié."""
    import logging
    from logging.handlers import RotatingFileHandler

    if not app.debug:
        handler = RotatingFileHandler(
            "logs/security.log",
            maxBytes=1_000_000,  # 1 Mo
            backupCount=5,
        )
        handler.setLevel(logging.WARNING)
        handler.setFormatter(logging.Formatter(
            "[%(asctime)s] %(levelname)s — %(message)s"
        ))
        app.logger.addHandler(handler)
        logging.getLogger().addHandler(handler)
