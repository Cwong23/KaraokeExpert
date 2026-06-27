from flask import Blueprint, request, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.app.apis.create_upload import get_url
from backend.app.apis.process_song import process
from backend.app.apis.get_song_status import get_status
from backend.app.apis.get_song_objects import get_urls
from backend.app.apis.get_completed_songs import get_completed_songs
from backend.app.apis.get_processing_songs import get_processing_songs
from http import HTTPStatus
from backend.app.utils.clients import container_client, mongo_client, redis_client, kafka_client
from marshmallow import Schema, fields, ValidationError, validate
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


song_bp = Blueprint('song_bp', __name__)

SONG_NAME_REGEX = r'^[a-zA-Z0-9]{1-100}$'
SONG_ID_REGEX = r'^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$'


class CreateUploadSchema(Schema):
    song_name = fields.Str(required=True, validate=validate.Regexp(
        SONG_NAME_REGEX,
    ))


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
    song_id = fields.Str(required=True, validate=validate.Regexp(
        SONG_ID_REGEX,
    ))


@song_bp.route("/process_song", methods=["PUT"])
@jwt_required()
@validate_body(ProcessSongSchema)
def process_song():
    r_client = redis_client()
    k_client = kafka_client()

    return process(r_client, k_client, get_jwt_identity(), g.validated)


@song_bp.route("/<song_id>/get_song_status", methods=["GET"])
@jwt_required()
def get_song_status(song_id):
    r_client = redis_client()

    return get_status(r_client, song_id)


@song_bp.route("/get_completed_songs", methods=["GET"])
@jwt_required()
def get_completed_songs():
    db_client = mongo_client()
    return get_completed_songs(db_client, get_jwt_identity())


@song_bp.route("/get_processing_songs", methods=["GET"])
@jwt_required()
def get_processing_songs():
    db_client = mongo_client()
    return get_processing_songs(db_client, get_jwt_identity())


@song_bp.route("/<song_id>/get_song_objects", methods=["GET"])
@jwt_required()
def get_song_objects(song_id):
    minio_client = container_client()
    return get_urls(minio_client, get_jwt_identity(), song_id)


@song_bp.route("/<song_id>/get_song_data", methods=["GET"])
@jwt_required()
def get_song_data(song_id):
    db_client = mongo_client()
    return get_urls(db_client, get_jwt_identity(), song_id)
