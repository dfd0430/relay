
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


def register_obda_routes(app, db):
    @app.route("/configure_sparql")
    def configure_sparql():
        db_id = request.args.get("db_id")
        if not db_id:
            return redirect(url_for("use_existing_db"))

        selected_db = db.get_db_connection_by_id(int(db_id))
        if not selected_db:
            return redirect(url_for("use_existing_db"))

        return render_template("configure_sparql.html", db=selected_db)

    @app.route("/use_existing_obda")
    def use_existing_obda():
        db_id = request.args.get("db_id")
        obda_blueprints = db.get_all_obda_configurations()
        return render_template("use_existing_obda.html", blueprints=obda_blueprints, db_id=db_id)

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

        return f"<h3>{file_type.upper()} File for {config['name']}</h3><pre>{decoded}</pre>"

    @app.route("/create_new_obda", methods=["GET", "POST"])
    def create_new_obda():
        db_id = request.args.get("db_id")
        message = None
        error = None

        if request.method == "POST":
            name = request.form.get("name")
            owl_file = request.files.get("owl_file")
            obda_file = request.files.get("obda_file")

            if not name or not owl_file or not obda_file:
                error = "All fields are required."
            else:
                owl_data = owl_file.read()
                obda_data = obda_file.read()
                timestamp = datetime.utcnow()

                db.insert_obda_configuration(name, owl_data, obda_data, timestamp)
                message = "OBDA blueprint saved successfully."

        return render_template("create_new_obda.html", message=message, error=error, db_id=db_id)