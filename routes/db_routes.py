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

        session["connection_info"] =  {
                    "is_temp": False,
                    "id": db_id,
                }

        return redirect(url_for("use_existing_obda"))

    @app.route("/create_new_db", methods=["GET", "POST"])
    def create_new_db():
        if request.method == "POST":
            action = request.form.get("action")
            name = request.form.get("name")
            jdbc_file = request.files.get("jdbc_file")
            properties_file = request.files.get("properties_file")

            if not jdbc_file or not properties_file or (action == "save_and_deploy" and not name):
                return render_template("create_new_db.html", error="All fields are required.")

            jdbc_data = jdbc_file.read()
            properties_data = properties_file.read()
            timestamp = datetime.now()

            if action == "save_and_deploy":
                # Permanent DB entry
                conn_id = db.insert_db_connection(name, jdbc_data, properties_data, timestamp)

                session["connection_info"] = {
                    "is_temp": False,
                    "id": conn_id,
                    "name":name
                }

            elif action == "deploy_only":

                conn_id = db.insert_temp_db_connection(name or "temp", jdbc_data, properties_data, timestamp)

                session["connection_info"] = {
                    "is_temp": True,
                    "id": conn_id,
                    "name": name
                }

            return redirect(url_for("use_existing_obda"))

        return render_template("create_new_db.html")

