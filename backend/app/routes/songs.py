from flask import Blueprint, current_app, jsonify, request, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.app.apis.create_upload import get_url
from backend.app.apis.process_song import process
from backend.app.apis.get_song_status import get_status
from http import HTTPStatus
from backend.app.utils.clients import container_client, mongo_client, redis_client, kafka_client
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
def create_upload():
    minio_client = container_client()
    db_client = mongo_client()
    r_client = redis_client()
    collection = db_client["karaokeexpert"]["songs"]

    if not minio_client:
        return {HTTPStatus.INTERNAL_SERVER_ERROR, {"message": "something went wrong"}}
    return get_url(minio_client, r_client, collection, get_jwt_identity(), g.validated)


class ProcessSongSchema(Schema):
    song_id = fields.Str(required=True)


@song_bp.route("/process_song", methods=["PUT"])
@jwt_required()
@validate_body(ProcessSongSchema)
def process_song():
    r_client = redis_client()
    k_client = kafka_client()

    return process(r_client, k_client, get_jwt_identity(), g.validated)


class GetSongStatusSchema(Schema):
    song_id = fields.Str(required=True)


@song_bp.route("/get_song_status", methods=["GET"])
@jwt_required()
@validate_body(ProcessSongSchema)
def get_song_status():
    r_client = redis_client()

    return get_status(r_client, get_jwt_identity(), g.validated)
