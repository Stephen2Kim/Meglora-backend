import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask import Blueprint, request, jsonify

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Correct the database URI format
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'meglora.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'your_secret_key'

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    print("App initialized with DB and JWT")
    
    # Import and register routes
    from app.routes import patient_routes, doctor_routes, auth_routes
    app.register_blueprint(patient_routes.bp)
    app.register_blueprint(doctor_routes.bp)
    app.register_blueprint(auth_routes.bp)  # Register the auth routes

    # Register the home route
    @app.route('/')
    def home():
        return jsonify({"message": "Welcome to the Meglora Backend!"}), 200

    return app

