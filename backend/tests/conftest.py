import pytest
from flask import Flask
from backend.app.routes.songs import song_bp
from flask_jwt_extended import JWTManager, create_access_token
from uuid import uuid4
# python -m pytest


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.update({
        "TESTING": True,
        "JWT_SECRET_KEY": str(uuid4())
    })

    JWTManager(app)
    app.register_blueprint(song_bp, url_prefix='/songs')

    return app


@pytest.fixture
def auth_headers(app):
    with app.app_context():
        token = create_access_token(identity="test_user")
        return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client(app):
    return app.test_client()
