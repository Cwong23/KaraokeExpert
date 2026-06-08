import os
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from backend.app.routes.songs import song_bp
from backend.app.routes.auth import auth_bp

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.environ["JWT_SECRET_KEY"]
app.config["JWT_TOKEN_LOCATION"] = ["headers"]

CORS(app)
jwt = JWTManager(app)

app.register_blueprint(song_bp, url_prefix='/songs')
app.register_blueprint(auth_bp, url_prefix="/auth")


if __name__ == '__main__':
    app.run()
