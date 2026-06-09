# python -m pytest
import pytest
from uuid import uuid4
from flask_jwt_extended import JWTManager, create_access_token
from backend.app.routes.songs import song_bp
from flask import Flask
import os
import mongomock
from unittest.mock import MagicMock


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


@pytest.fixture(scope="session")
def mock_minio_client():
    mock_minio = MagicMock()
    yield mock_minio


@pytest.fixture(scope="session")
def mock_redis_client():
    mock_redis = MagicMock()
    yield mock_redis


@pytest.fixture(scope="session")
def test_db_client():
    client = mongomock.MongoClient()
    yield client
    client.close()


@pytest.fixture(scope="function")
def test_db(test_db_client):
    db_name = "karaokeexpert"
    db = test_db_client[db_name]

    yield db

    for collection_name in db.list_collection_names():
        db[collection_name].drop()
