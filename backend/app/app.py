import os
from flask import Flask
from routes.songs import song_bp

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.environ["JWT_SECRET_KEY"]
app.config["JWT_TOKEN_LOCATION"] = ["headers"]

app.register_blueprint(song_bp, url_prefix='/songs')


if __name__ == '__main__':
    app.run()
