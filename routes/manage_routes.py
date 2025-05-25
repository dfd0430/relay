
import os
import json
from SPARQLWrapper import SPARQLWrapper, JSON
from flask import Flask, request, render_template, redirect, url_for,jsonify, flash
from docker_functions import *
from werkzeug.utils import secure_filename
from SQLiteDB import *
from ontop import deploy_ontop_container
from datetime import datetime
import pytz
from flask import render_template

def register_manage_routes(app, db):

    @app.route("/manage_db_connections", methods=["GET"])
    def manage_db_connections():
        db_connections = db.get_all_db_connections()
        return render_template("manage_db_connections.html", connections=db_connections)

    @app.route("/delete_db_connection", methods=["POST"])
    def delete_db_connection():
        db_id = request.form.get("db_id")
        if db_id:
            db.delete_db_connection(int(db_id))
        return redirect(url_for("manage_db_connections"))

    @app.route("/create_new_db_manage", methods=["GET", "POST"])
    def create_new_db_manage():
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
        return render_template("create_new_db_manage.html", message=message, error=error)

    @app.route("/manage_blueprints")
    def manage_blueprints():
        obda_blueprints = db.get_all_obda_configurations()
        return render_template("manage_blueprints.html", obda_blueprints=obda_blueprints)

    @app.route("/delete_blueprint", methods=["POST"])
    def delete_blueprint():
        blueprint_id = request.form.get("blueprint_id")
        if blueprint_id:
            db.delete_blueprint(int(blueprint_id))  # You'll implement this method below
        return redirect(url_for("manage_blueprints"))

    @app.route("/create_new_obda_manage", methods=["GET", "POST"])
    def create_new_obda_manage():
        message = None
        error = None

        if request.method == "POST":
            name = request.form.get("name")
            description = request.form.get("description")  # New field
            owl_file = request.files.get("owl_file")
            obda_file = request.files.get("obda_file")

            if not name or not description or not owl_file or not obda_file:
                error = "All fields are required."
            else:
                owl_data = owl_file.read()
                obda_data = obda_file.read()
                timestamp = datetime.utcnow()

                db.insert_obda_configuration(name, description, owl_data, obda_data, timestamp)
                message = "OBDA blueprint saved successfully."

        return render_template("create_new_obda_manage.html", message=message, error=error)

    @app.route("/all_logs_overview")
    def all_logs_overview():
        containers = db.get_all_unique_containers()
        return render_template("logs_overview.html", containers=containers)
