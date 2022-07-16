from uuid import uuid4
import json
from random import randint

from flask import Flask, jsonify, abort
from flask_redis import FlaskRedis
from flask_migrate import Migrate
from sqlalchemy import func

import settings

from application.decorators import token_required, admin_token_required
from application.models import *


migrate = Migrate()
redis_client = FlaskRedis()


def create_app(config_object=settings.ProdConfig):
    app = Flask(__name__)
    app.config.from_object(config_object)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    migrate.init_app(app, db)

    @app.route("/points", methods=["GET"])
    @token_required
    def points_list(user_id):
        points = Point.query.all()
        return jsonify({"points": [{"latitude": point.latitude,
                                   "longitude": point.longitude,
                                   "description": point.description} for point in points]})

    @app.route("/routes/generate/from/<int:point_from_id>/to/<int:point_to_id>", methods=["POST"])
    @token_required
    def route_generate(user_id, point_from_id, point_to_id):
        if not Point.query.filter_by(id=point_from_id).first():
            return jsonify({"message": "Point from doesn't exist"}), 404

        if not Point.query.filter_by(id=point_to_id).first():
            return jsonify({"message": "Point to doesn't exist"}), 404

        request_id = str(uuid4())
        data = {
            "request_id": request_id,
            "point_from_id": point_from_id,
            "point_to_id": point_to_id,
            "user_id": user_id
        }
        redis_client.lpush(settings.ROUTES_QUEUE_REDIS_KEY, json.dumps(data))
        redis_client.sadd(settings.ROUTES_INPROGRESS_REDIS_KEY, request_id)
        
        return jsonify({"request_id": request_id})

    @app.route("/route-requests/<string:request_id>/status", methods=["GET"])
    @token_required
    def routes_request_status(user_id, request_id):
        is_processing = redis_client.sismember(settings.ROUTES_INPROGRESS_REDIS_KEY, request_id)
        if is_processing:
            return jsonify({"status": "processing"})

        route = Route.query.options(db.joinedload(Route.points)).filter_by(request_id=request_id).first()

        if route:            
            return jsonify({
                "status": "done",
                "route_id": route.id,
                "user_id": route.user_id,
                "points": [{"latitude": point.latitude,
                            "longitude": point.longitude,
                            "description": point.description} for point in route.points]
                })

        else:
            return jsonify({"message": "Request not found"}), 404

    @app.route("/routes", methods=["GET"])
    @token_required
    def routes_list(user_id):
        routes = Route.query.all()
        return jsonify({"routes": [{"route_id": route.id, "user_id": route.user_id} for route in routes]})

    @app.route("/routes/<int:route_id>", methods=["GET"])
    @token_required
    def route_data(user_id, route_id):
        route = Route.query.options(db.joinedload(Route.points)).filter_by(id=route_id).first()

        if route:
            return jsonify({
                "route_id": route.id,
                "user_id": route.user_id,
                "points": [{"latitude": point.latitude,
                            "longitude": point.longitude,
                            "description": point.description} for point in route.points]
                })

        else:
            return jsonify({"message": "Request not found"}), 404

    @app.route("/routes/stats", methods=["GET"])
    @token_required
    def routes_stats(user_id):
        stats = db.session.query(Route.user_id.label('user_id'), func.count().label('points_count')).join(route_points).group_by(Route.user_id).all()
        return jsonify({"stats": [{"user_id": item.user_id, "points_count": item.points_count} for item in stats]})

    @app.route("/import")
    @admin_token_required
    def init_import(user_id):
        min_value = 0
        max_value = 100
        count = 1000000

        points = []
        for i in range(count):
            points.append(Point(latitude=randint(min_value, max_value), longitude=randint(min_value, max_value)))

        db.session.add_all(points)
        db.session.commit()

        return jsonify({"status": "done"})

    return app


if __name__ == "__main__":
    app = create_app()
    redis_client.init_app(app)

    app.run(host='127.0.0.1', port='5001')

