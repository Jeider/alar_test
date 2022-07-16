ROUTES_QUEUE_REDIS_KEY = "route_requests"
ROUTES_INPROGRESS_REDIS_KEY = "route_request_inprogress"

SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://alar_test:password@localhost/alar_points'

SLEEP_TIMEOUT = 1


class ProdConfig:
    ENV = "prod"
    DEBUG = False


class DevConfig:
    ENV = "dev"
    DEBUG = True


class TestConfig:
    TESTING = True
    DEBUG = True
