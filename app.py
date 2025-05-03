import os
import json
from SPARQLWrapper import SPARQLWrapper, JSON
from flask import Flask, request, render_template, redirect, url_for,jsonify
from docker_functions import *
from werkzeug.utils import secure_filename
from SQLiteDB import *
from ontop import deploy_ontop_container

app = Flask(__name__)
DATA_FILE = "combined_containers.json"
Network = os.getenv("Network", "database-net")
LOG_FILE = "query_logs.jsonl"

UPLOAD_FOLDER = "/tmp/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs("/volume/backup", exist_ok=True)
db = SQLiteDB("sqlite:////volume/backup/my_database.db")

db.create_blueprint_table()

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
    dind_containers = list_dind_containers()
    combinations = load_combinations()

    if request.method == "POST":
        obda = request.files.get("obda_file")
        owl = request.files.get("owl_file")
        properties = request.files.get("properties_file")
        jdbc = request.files.get("jdbc_file")
        selected_dind = request.form.get("dind_container")

        if not obda or not owl or not properties or not jdbc or not selected_dind:
            return jsonify({"error": "All fields including DIND selection are required"}), 400

        obda_path = os.path.join("/volume/ontop_input", "mappings.obda")
        owl_path = os.path.join("/volume/ontop_input", "ontologie.owl")
        prop_path = os.path.join("/volume/ontop_input", "database.properties")
        jdbc_path = os.path.join("/volume/ontop_jdbc", "driver.jar")

        obda.save(obda_path)
        owl.save(owl_path)
        properties.save(prop_path)
        jdbc.save(jdbc_path)

        ontop_name = deploy_ontop_container(obda_path, owl_path, prop_path)  # Assuming it does not yet use jdbc_path

        obda_data = obda.read() if obda else None
        owl_data = owl.read() if owl else None
        properties_data = properties.read() if properties else None
        jdbc_data = jdbc.read() if jdbc else None
        db.insert_blueprint("testtest", obda_data, owl_data, properties_data, jdbc_data)

        new_combo = {
            "network_container": ontop_name,
            "dind_container": selected_dind
        }

        if new_combo not in combinations:
            combinations.append(new_combo)
            save_combinations(combinations)

    return render_template(
        "query_form.html",
        dind_containers=dind_containers,
        combined_containers=combinations
    )



@app.route("/logs/<container_name>")
def view_logs(container_name):
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            for line in f:
                entry = json.loads(line)
                if entry["container_name"] == container_name:
                    logs.append(entry)
    else:
        logs = []

    return render_template("logs.html", container_name=container_name, logs=logs)

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



@app.route("/init", methods=["POST"])
def initialize():
    try:
        setup_nginx()

        return redirect(url_for('index', setup_result="Setup complete!"))
    except Exception as e:

        return redirect(url_for('index', setup_result=f"Setup failed: {str(e)}"))




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
    except Exception as e:
        return jsonify({"error": "Deployment failed", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
