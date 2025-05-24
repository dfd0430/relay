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

def register_logic_routes(app, db):
    @app.route("/remove", methods=["POST"])
    def remove_combination():
        to_remove = request.form.get("to_remove")
        combinations = load_combinations()

        if to_remove:
            # We expect format: "network_name|dind_name"
            net_name, dind_name = to_remove.split("|")

            # Stop the network container
            stop_docker_container(net_name)

            # Optionally stop dind container too
            # stop_docker_container(dind_name)

            # Remove from combinations
            combinations = [
                c for c in combinations
                if not (c["network_container"] == net_name and c["dind_container"] == dind_name)
            ]
            save_combinations(combinations)

        return redirect(url_for("index"))

    @app.route("/query", methods=["POST", "GET"])
    def handle_query():
        try:
            client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
            container_info = get_container_name_by_ip(client_ip)
            container_id = container_info["id"]
            container_name = container_info["name"]
            network_container = find_network_container(container_id)

            if network_container is None:
                raise ValueError(f"Unsupported container name for IP {client_ip}")

            sparql = SPARQLWrapper(f"http://{network_container}:8080/sparql")

            if request.method == "POST":
                incoming_data = request.get_json()
                if not incoming_data or "query" not in incoming_data:
                    return jsonify({"error": "Missing query parameter"}), 400
                sparql_query = incoming_data["query"]
            elif request.method == "GET":
                sparql_query = request.args.get("query")
                if not sparql_query:
                    return jsonify({"error": "Missing query parameter"}), 400

            # log_ip(client_ip, sparql_query)
            log_query(client_ip, container_name,container_id, sparql_query, db)

            sparql.setQuery(sparql_query)
            sparql.setReturnFormat(JSON)
            results = sparql.queryAndConvert()

            return jsonify(results)

        except Exception as e:
            return (
                jsonify({"error": "An unexpected error occurred", "details": str(e)}),
                500,
            )
        except Exception as e:
            return jsonify({"error": "Deployment failed", "details": str(e)}), 500

