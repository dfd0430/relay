import os
import json
from SPARQLWrapper import SPARQLWrapper, JSON
from flask import Flask, request, render_template, redirect, url_for,jsonify
from docker_functions import *

LOG_FILE = "query_logs.jsonl"
app = Flask(__name__)
DATA_FILE = "combined_containers.json"
Network = os.getenv("Network", "database-net")


def load_combinations():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []


def save_combinations(combos):
    with open(DATA_FILE, "w") as f:
        json.dump(combos, f, indent=2)

def log_query(ip, container_name, query):
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "ip": ip,
        "container_name": container_name,
        "query": query,
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

@app.route("/", methods=["GET", "POST"])
def index():
    network_containers = list_containers_on_network(Network)
    dind_containers = list_dind_containers()
    combinations = load_combinations()

    if request.method == "POST":
        selected_network = request.form.get("network_container")
        selected_dind = request.form.get("dind_container")

        if selected_network and selected_dind:
            new_combo = {
                "network_container": selected_network,
                "dind_container": selected_dind
            }

            if new_combo not in combinations:
                combinations.append(new_combo)
                save_combinations(combinations)

        return redirect(url_for("index"))

    return render_template(
        "query_form.html",
        network_containers=network_containers,
        dind_containers=dind_containers,
        combined_containers=combinations
    )


@app.route("/remove", methods=["POST"])
def remove_combination():
    to_remove = request.form.get("to_remove")
    combinations = load_combinations()

    if to_remove:
        # We expect format: "network_name|dind_name"
        net_name, dind_name = to_remove.split("|")
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
        container_name = get_container_name_by_ip(client_ip)
        network_container = find_network_container(container_name)

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
        log_query(client_ip, container_name, sparql_query)

        sparql.setQuery(sparql_query)
        sparql.setReturnFormat(JSON)
        results = sparql.queryAndConvert()

        return jsonify(results)

    except Exception as e:
        return (
            jsonify({"error": "An unexpected error occurred", "details": str(e)}),
            500,
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
