import html

from flask import request, render_template, redirect, url_for, jsonify
from SPARQLWrapper import SPARQLWrapper, JSON
from datetime import datetime
import pytz
import os
import json
from docker_functions import *
from SQLiteDB import *
from ontop import deploy_ontop_container
from utils import load_combinations, save_combinations, log_query
from flask import session


def register_obda_routes(app, db):
    @app.route("/configure_sparql")
    def configure_sparql():
        selected_db= session.get("connection_info", {}).get("name")

        return render_template("configure_sparql.html", selected_db=selected_db)

    @app.route("/use_existing_obda")
    def use_existing_obda():
        obda_blueprints = db.get_all_obda_configurations()
        return render_template("use_existing_obda.html", blueprints=obda_blueprints)

    @app.route("/view_obda_file/<int:obda_id>/<file_type>")
    def view_obda_file(obda_id, file_type):
        config = db.get_obda_configuration_by_id(obda_id)
        if not config or file_type not in ["owl", "obda"]:
            return "Invalid request", 404

        content = config["owl_file"] if file_type == "owl" else config["obda_file"]
        try:
            decoded = content.decode("utf-8")
        except UnicodeDecodeError:
            decoded = "[Binary content — not displayable as text]"

        # Escape special HTML characters
        escaped = html.escape(decoded)

        return f"<h3>{file_type.upper()} File for {config['name']}</h3><pre>{escaped}</pre>"

    @app.route("/create_new_obda", methods=["GET", "POST"])
    def create_new_obda():
        db_id = request.args.get("db_id")
        message = None
        error = None

        if request.method == "POST":
            name = request.form.get("name")
            description = request.form.get("description")  # NEW
            owl_file = request.files.get("owl_file")
            obda_file = request.files.get("obda_file")
            action = request.form.get("action")

            if not owl_file or not obda_file or (action == "save_and_select" and (not name or not description)):
                error = "All fields are required."
            else:
                owl_data = owl_file.read()
                obda_data = obda_file.read()
                timestamp = datetime.utcnow()

                if action == "save_and_select":
                    obda_id = db.insert_obda_configuration(name, description, owl_data, obda_data, timestamp)
                    session["selected_obda"] = {
                        "id": obda_id,
                        "is_temp": False,
                        "name": name
                    }
                else:
                    obda_id = db.insert_temp_obda_configuration(name, description, owl_data, obda_data, timestamp)
                    session["selected_obda"] = {
                        "id": obda_id,
                        "is_temp": True,
                        "name": name
                    }

                return redirect(url_for("select_train"))

        return render_template("create_new_obda.html", error=error, message=message, db_id=db_id)

    @app.route("/select_obda", methods=["POST"])
    def select_obda():
        obda_id = request.form.get("obda_id")
        if not obda_id:
            return redirect(url_for("use_existing_obda"))  # fallback if no selection

        session["selected_obda"] = {
            "id": int(obda_id),
            "is_temp": False,

        }
        return redirect(url_for("select_train"))