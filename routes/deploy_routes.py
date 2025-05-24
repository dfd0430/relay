
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
        selected_train = request.form.get("selected_train")
        if not selected_train:
            return redirect(url_for("select_train"))

        session["selected_train"] = selected_train
        return redirect(url_for("train_ready"))


    @app.route("/train_ready")
    def train_ready():
        # 1. Pull context out of session
        obda_id = session.get("selected_obda_id")
        db_id = session.get("selected_db_id")
        dind_container = session.get("selected_train")

        # 2. Validate
        if not obda_id or not db_id or not dind_container:
            return redirect(url_for("select_train"))

        # 3. Fetch files from DB
        obda_cfg = db.get_obda_configuration_by_id(obda_id)
        db_conn = db.get_db_connection_by_id(db_id)
        if not obda_cfg or not db_conn:
            return redirect(url_for("select_train"))

        obda_data = obda_cfg["obda_file"]
        owl_data = obda_cfg["owl_file"]
        properties_data = db_conn["properties_file"]
        jdbc_data = db_conn["jdbc_file"]

        # 4. Write files out for deployment
        #    (make sure these directories exist and are volume-mounted)

        # 5. Deploy your Ontop container
        ontop_name = deploy_ontop_container(obda_data, owl_data, properties_data, jdbc_data)

        combinations = load_combinations()
        new_combo = {
            "network_container": ontop_name,
            "dind_container": dind_container
        }
        if new_combo not in combinations:
            combinations.append(new_combo)
            save_combinations(combinations)

        return f"<h3>Deployed Ontop container: <code>{ontop_name}</code></h3>"

