from flask import Flask
from flask_cors import CORS

from app.config import Config
from app.extensions import db


def create_app(config_class: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})
    db.init_app(app)

    from app.routes.health import bp as health_bp
    from app.routes.jobs import bp as jobs_bp
    from app.routes.saved import bp as saved_bp
    from app.routes.alerts import bp as alerts_bp
    from app.routes.employers import bp as employers_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(jobs_bp, url_prefix="/api/jobs")
    app.register_blueprint(saved_bp, url_prefix="/api/saved")
    app.register_blueprint(alerts_bp, url_prefix="/api/alerts")
    app.register_blueprint(employers_bp, url_prefix="/api/employers")

    with app.app_context():
        db.create_all()
        if app.config.get("SEED_DEMO_JOBS"):
            from app.services.seed import seed_demo_jobs

            seed_demo_jobs()

    return app
