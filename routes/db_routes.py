from flask import request, render_template, redirect, url_for, jsonify
from SPARQLWrapper import SPARQLWrapper, JSON
from datetime import datetime
import pytz
import os

from docker_functions import *
from SQLiteDB import *
from ontop import deploy_ontop_container
from utils import load_combinations, save_combinations, log_query


def register_db_routes(app, db):
    @app.route("/create_db")
    def create_db():
        db_connections = db.get_all_db_connections()
        return render_template("create_db.html", connections=db_connections)

    from flask import session

    @app.route("/select_db_connection", methods=["POST"])
    def select_db_connection():
        db_id = request.form.get("db_id")

        if not db_id:
            return redirect(url_for("use_existing_db"))
        selected_db = db.get_db_connection_by_id(int(db_id))
        if not selected_db:
            return redirect(url_for("use_existing_db"))

        session["selected_db_id"] = db_id

        return redirect(url_for("configure_sparql"))

    @app.route("/create_new_db", methods=["GET", "POST"])
    def create_new_db():
        message = None
        error = None
        if request.method == "POST":
            name = request.form.get("name")
            jdbc_file = request.files.get("jdbc_file")
            properties_file = request.files.get("properties_file")
            if not name or not jdbc_file or not properties_file:
                error = "All fields are required."
            else:
                jdbc_data = jdbc_file.read()
                properties_data = properties_file.read()
                timestamp = datetime.utcnow()
                db.insert_db_connection(name, jdbc_data, properties_data, timestamp)
                message = "Database connection saved successfully."
        return render_template("create_new_db.html", message=message, error=error)
