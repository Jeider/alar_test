from flask import Flask, jsonify
import jwt

import settings


def create_app(config_object=settings.ProdConfig):
    app = Flask(__name__)
    app.config.from_object(config_object)

    @app.route("/login/<int:user_id>", methods=["POST"])
    def login(user_id):
        return jwt.encode({"user_id": user_id, "superadmin": False}, settings.AUTH_SECRET, algorithm=settings.AUTH_ENCODING)

    @app.route("/login-admin/<int:user_id>", methods=["POST"])
    def login_admin(user_id):
        return jwt.encode({"user_id": user_id, "superadmin": True}, settings.AUTH_SECRET, algorithm=settings.AUTH_ENCODING)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host='127.0.0.1', port='5000')
