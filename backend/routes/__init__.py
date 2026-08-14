"""Route modules. URL layer only: read request -> call service -> return JSON."""

from . import evaluation, review, settings, upload


def register_routes(app):
    upload.register_routes(app)
    evaluation.register_routes(app)
    review.register_routes(app)
    settings.register_routes(app)