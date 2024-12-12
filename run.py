# run.py

from app import create_app
from flask import Blueprint, render_template

# Create the Flask application using the factory function
app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
