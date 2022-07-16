from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


route_points = db.Table(
    'route_points',
    db.Column('id', db.Integer(), primary_key=True),
    db.Column('point_id', db.Integer(), db.ForeignKey('points.id')),
    db.Column('route_id', db.Integer(), db.ForeignKey('routes.id'))
)

class Route(db.Model):
    __tablename__ = "routes"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    request_id = db.Column(db.String(36), unique=True, nullable=False)

    points = db.relationship('Point', secondary=route_points, lazy='subquery', backref=db.backref('routes', lazy=True))

    def __repr__(self):
        return '<Route %r>' % self.request_id


class Point(db.Model):
    __tablename__ = "points"
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255))

    def __repr__(self):
        return '<Point %r>' % self.description
