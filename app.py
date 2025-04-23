import os
import json
from flask import Flask, request, render_template, redirect, url_for
from docker_functions import *

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
