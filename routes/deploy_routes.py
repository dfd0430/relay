
import os
import json
from SPARQLWrapper import SPARQLWrapper, JSON
from flask import Flask, request, render_template, redirect, url_for,jsonify, flash,session
from docker_functions import *
from werkzeug.utils import secure_filename
from SQLiteDB import *
from ontop import deploy_ontop_container, save_deployment_files
from datetime import datetime
import pytz

from utils import load_combinations, save_combinations


def register_deploy_routes(app, db):
    @app.route("/select_train")
    def select_train():
        dind_containers = list_dind_containers()  # your custom function
        return render_template("select_train.html", dind_containers=dind_containers)

    @app.route("/train_selection", methods=["POST"])
    def train_selection():
        selected = request.form.get("selected_train")  # e.g. "abc123|my_container"
        if not selected:
            return redirect(url_for("select_train"))

        container_id, container_name = selected.split("|", 1)
        session["selected_train"] = {
            "id": container_id,
            "name": container_name
        }

        return redirect(url_for("train_ready"))

    @app.route("/train_ready")
    def train_ready():
        # 1. Pull context from session
        obda_info = session.get("selected_obda", {})
        connection_info = session.get("connection_info", {})
        dind_container_info = session.get("selected_train")

        obda_id = obda_info.get("id")
        obda_is_temp = obda_info.get("is_temp", False)

        db_id = connection_info.get("id")
        db_is_temp = connection_info.get("is_temp", False)

        # 2. Validate session state
        if not obda_id or not db_id or not dind_container_info:
            print(1)
            return redirect(url_for("select_train"))

        # 3. Fetch OBDA
        if obda_is_temp:
            obda_cfg = db.get_temp_obda_configuration_by_id(obda_id)
        else:
            obda_cfg = db.get_obda_configuration_by_id(obda_id)

        # 4. Fetch DB connection
        if db_is_temp:
            db_conn = db.get_temp_db_connection_by_id(db_id)
        else:
            db_conn = db.get_db_connection_by_id(db_id)

        # 5. Validation
        if not obda_cfg or not db_conn:
            print(2)
            return redirect(url_for("select_train"))

        # 6. Extract file content
        obda_data = obda_cfg["obda_file"]
        owl_data = obda_cfg["owl_file"]
        properties_data = db_conn["properties_file"]
        jdbc_data = db_conn["jdbc_file"]

        # 7. Deploy container
        ontop_name = deploy_ontop_container(obda_data, owl_data, properties_data, jdbc_data)

        # 8. Track combo
        combinations = load_combinations()
        new_combo = {
            "network_container": ontop_name,
            "dind_container": dind_container_info.get("id")
        }
        if new_combo not in combinations:
            combinations.append(new_combo)
            save_combinations(combinations)

        session["latest_train"] = new_combo

        return redirect(url_for("train_status"))

    @app.route("/train_status")
    def train_status():
        train = session.get("latest_train")
        if not train:
            return "No recent deployment found.", 404
        return render_template("train_status.html", train=train)

    @app.route("/logs_deployment/<container_name>")
    def view_logs_deployment(container_name):
        try:
            logs = db.get_logs_by_container(container_name)
            return render_template("logs_deployment.html", container_name=container_name, logs=logs)
        except Exception as e:
            return f"Error retrieving logs: {e}", 500