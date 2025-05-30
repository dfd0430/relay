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

    @app.route("/logs_manage_deployments/<container_id>")
    def view_logs_manage_deployments(container_id):
        try:
            logs = db.get_logs_by_container(container_id)
            return render_template("logs_manage_deployments.html", container_id=container_id, logs=logs)
        except Exception as e:
            return f"Error retrieving logs: {e}", 500

    @app.route("/logs/<container_id>")
    def view_logs(container_id):
        try:
            logs = db.get_logs_by_container(container_id)
            return render_template("logs.html", container_id=container_id, logs=logs)
        except Exception as e:
            return f"Error retrieving logs: {e}", 500


