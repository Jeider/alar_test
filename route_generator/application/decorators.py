from functools import wraps

from flask import request, jsonify
import jwt

import settings


def token_required(func):

    @wraps(func)
    def decorator(*args, **kwargs):
        token = None

        if 'x-access-tokens' in request.headers:
           token = request.headers['x-access-tokens']
 
        if not token:
            return jsonify({'message': 'token is not found'}), 401
        try:
            decoded = jwt.decode(token, settings.AUTH_SECRET, algorithms=[settings.AUTH_ENCODING])
            kwargs['user_id'] = decoded['user_id']
        except:
            return jsonify({'message': 'token is invalid'}), 401
 
        return func(*args, **kwargs)
    return decorator
