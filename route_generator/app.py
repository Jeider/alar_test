import json
import random
from threading import Thread
from time import sleep

from flask import Flask, jsonify, abort
from flask_redis import FlaskRedis
from sqlalchemy.sql.expression import func, select
from sqlalchemy.sql import exists

import settings

from application.models import *


MIN_POINTS = 2
MAX_POINTS = 100

thread_is_active = False


redis_client = FlaskRedis()

def get_route_request():
    data = redis_client.lindex(settings.ROUTES_QUEUE_REDIS_KEY, 0)
    if data:
        return json.loads(data)


def complete_route_request(request_id):
    redis_client.lpop(settings.ROUTES_QUEUE_REDIS_KEY)
    redis_client.srem(settings.ROUTES_INPROGRESS_REDIS_KEY, request_id)


def find_middle_points(point_from_id, point_to_id):
    route_points_count = random.randint(MIN_POINTS, MAX_POINTS)
    return Point.query.filter(Point.id.notin_([point_from_id, point_to_id])).order_by(func.random()).limit(route_points_count).all()


def get_first_point(point_from_id):
    return Point.query.filter_by(id=point_from_id).first()


def get_last_point(point_to_id):
    return Point.query.filter_by(id=point_to_id).first()


def get_route(user_id, request_id):
    return Route.query.filter_by(user_id=user_id, request_id=request_id).first()


def generate_route():
    request = get_route_request()

    if request is not None:

        with app.app_context():
            user_id = request['user_id']
            request_id = request['request_id']
            point_from_id = request['point_from_id']
            point_to_id = request['point_to_id']

            if get_route(user_id, request_id) is not None:
                # TODO: log "route already exist"
                complete_route_request(request_id)
                return

            first_point = get_first_point(point_from_id)
            last_point = get_last_point(point_to_id)

            if first_point is None or last_point is None:
                # TODO: log "points not found"
                complete_route_request(request_id)
                return

            middle_points = find_middle_points(point_from_id, point_to_id)

            route = Route(user_id=user_id, request_id=request_id)

            route.points.append(first_point)
            for point in middle_points:
                route.points.append(point)
            route.points.append(last_point)

            db.session.add(route)
            db.session.commit()

            # TODO: log "task completed"
            complete_route_request(request_id)


def create_app(config_object=settings.ProdConfig):
    app = Flask(__name__)
    app.config.from_object(config_object)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    redis_client.init_app(app)

    @app.route("/status")
    def status():
        return jsonify({"status": "ok"})

    def run():
        while True:
            sleep(int(settings.SLEEP_TIMEOUT))
            generate_route()

    def run_thread():
        t = Thread(target=run, args=())
        t.daemon = True
        t.start()

    run_thread()

    return app


if __name__ == "__main__":
    app = create_app()

    app.run(host='127.0.0.1', port='5005')
