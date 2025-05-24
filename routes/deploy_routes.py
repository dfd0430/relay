
import os
import json
from SPARQLWrapper import SPARQLWrapper, JSON
from flask import Flask, request, render_template, redirect, url_for,jsonify, flash,session
from docker_functions import *
from werkzeug.utils import secure_filename
from SQLiteDB import *
from ontop import deploy_ontop_container
from datetime import datetime
import pytz

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
        selected = session.get("selected_train")
        if not selected:
            return redirect(url_for("select_train"))

        return f"<h3>Train environment <code>{selected}</code> is selected and ready!</h3>"
