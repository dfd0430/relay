
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
            return redirect(url_for("select_train"))

        # 3. Fetch OBDA
        if obda_is_temp:
            obda_cfg = db.get_temp_obda_configuration_by_id(obda_id)
        else:
            obda_cfg = db.get_obda_configuration_by_id(obda_id)

        # 4. Fetch DB connection
        if db_is_temp:
            db_conn = db.get_temp_db_connection_by_id(db_id)
            db_name = db_conn["name"] if db_conn else None
            session["latest_conn"] = db_conn["name"] if db_conn else None
        else:
            db_conn = db.get_db_connection_by_id(db_id)
            db_name = db_conn["name"] if db_conn else None
            session["latest_conn"] = db_conn["name"] if db_conn else None
        # 5. Validation
        if not obda_cfg or not db_conn:
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

        combinations = [c for c in combinations if c["dind_container"] != new_combo["dind_container"]]

        if new_combo not in combinations:
            combinations.append(new_combo)
            save_combinations(combinations)

        if db_is_temp:
            db.delete_temp_db_connection(db_id)

        if obda_is_temp:
            db.delete_temp_obda_configuration(obda_id)
        obda_name = obda_info.get("name")
        db.insert_ontop_connection(ontop_name,db_name,obda_name)

        session.pop("selected_obda")
        session.pop("connection_info")
        session.pop("selected_train")



        session["latest_train"] = dind_container_info
        session["latest_network_name"] = ontop_name
        return redirect(url_for("train_status"))

    @app.route("/train_status")
    def train_status():
        train_info = session.get("latest_train")
        ontop_name = session.get("latest_network_name")
        db_name = session.get("latest_conn")
        obda_name = db.get_selected_obda(ontop_name)
        if not train_info:
            return "No recent deployment found.", 404
        return render_template("train_status.html", train=train_info, ontop_name=ontop_name, obda_name=obda_name, db_name=db_name)

    @app.route("/logs_deployment/<container_id>")
    def view_logs_deployment(container_id):
        try:
            logs = db.get_logs_by_container(container_id)
            container_name = db.get_container_name_by_id(container_id)  # <- Use your actual method to fetch name
            return render_template("logs_deployment.html", container_id=container_id, container_name=container_name,
                                   logs=logs)
        except Exception as e:
            return f"Error retrieving logs: {e}", 500

    @app.route("/view_ontop_logs/<string:ontop_name>")
    def view_ontop_logs(ontop_name):
        """
        Renders a page displaying the logs for a specific Docker container by Name.
        This is intended for the 'Ontop' (VKG) container.
        """
        container_logs, log_status_message, container_name = get_container_logs_by_name(ontop_name)

        # Use the same template as view_logs_deployment for consistency in display
        return render_template(
            "view_ontop_logs.html",  # Reusing the same log display template
            container_id="N/A (by name)",  # Indicate it was fetched by name, ID might not be directly available in URL
            container_name=container_name,
            container_logs=container_logs,
            log_status_message=log_status_message
        )

    @app.route("/check_vkg_connection_status/<string:ontop_name>")
    def check_vkg_connection_status(ontop_name):
        logs, status_message, _ = get_container_logs_by_name(ontop_name)

        # Define the success and error keywords
        success_keyword = "Started OntopEndpointApplication"  # Example keyword for success
        error_keyword = "ERROR"  # Example keyword for general errors

        if success_keyword in logs:
            return jsonify({"status": "connected",
                            "message": "✅ The VKG and Train containers are now connected. You can start the Train when ready."})
        elif error_keyword in logs:
            return jsonify(
                {"status": "error", "message": ("❌ An error occurred starting up the VKG. "
            " Please check your Database Connection and OBDA configuration files. "
            " For more details, refer to the logs of the VKG container.")})
        else:
            return jsonify({"status": "connecting", "message": "⏳ Connecting VKG container..."})

    @app.route("/check_vkg_query/<string:ontop_name>")
    def check_vkg_query(ontop_name):
        logs, status_message, _ = get_container_logs_by_name(ontop_name)

        # Define the error keyword
        error_keyword = "Exception"  # Keyword to check for errors

        if error_keyword in logs:
            return jsonify(
                {"status": "error",
                 "message": ("❌ An Exception occurred in the VKG container during query execution."
                 " For more details, refer to the logs of the VKG container.")})
        else:
            # IMPORTANT: Return a non-error status when no exception is found.
            # The message here doesn't matter much since the JS won't display it.
            return jsonify({"status": "no_error", "message": "No exceptions found."})
