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

def register_random_routes(app, db):

    @app.route("/deployments")
    def list_deployments():
        combinations = load_combinations()
        return render_template("deployments.html", combined_containers=combinations)

    @app.route("/logs/<container_name>")
    def view_logs(container_name):
        try:
            logs = db.get_logs_by_container(container_name)
            return render_template("logs.html", container_name=container_name, logs=logs)
        except Exception as e:
            return f"Error retrieving logs: {e}", 500


