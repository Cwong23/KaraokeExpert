from flask import Blueprint, current_app, jsonify, request, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.apis.create_multipart_upload import create_upload
from http import HTTPStatus
from app.utils.clients import container_client, mongo_client
from marshmallow import Schema, fields, ValidationError
from functools import wraps


def validate_body(schema_class):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                g.validated = schema_class().load(request.get_json() or {})
            except ValidationError as e:
                return {"errors": e.messages}, 400
            return f(*args, **kwargs)
        return wrapper
    return decorator


class CreateUploadSchema(Schema):
    song_name = fields.Str(required=True)


song_bp = Blueprint('song_bp', __name__)


@song_bp.route("/create_upload", methods=["POST"])
@jwt_required()
@validate_body(CreateUploadSchema)
def create_multipart_upload():
    minio_client = container_client()
    db_client = mongo_client()
    collection = db_client["karaokeexpert"]["songs"]

    if not minio_client:
        return {HTTPStatus.INTERNAL_SERVER_ERROR, {"message": "something went wrong"}}
    return create_upload(minio_client, collection, get_jwt_identity(), g.validated)
