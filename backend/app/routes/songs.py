from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.app.apis.create_multipart_upload import create_upload
from http import HTTPStatus
from backend.app.utils.clients import container_client

song_bp = Blueprint('song_bp', __name__)


@song_bp.route("/create_upload", methods=["POST"])
@jwt_required()
def create_multipart_upload():
    client = container_client()

    if not client:
        return HTTPStatus.INTERNAL_SERVER_ERROR
    return create_upload(client, get_jwt_identity())
