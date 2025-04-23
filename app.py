import os
import json
from flask import Flask, request, render_template
from SPARQLWrapper import SPARQLWrapper, JSON

from docker_functions import *

app = Flask(__name__)

SPARQL_ENDPOINT = os.getenv("SPARQL_ENDPOINT", "http://localhost:8080/sparql")
Network = os.getenv("Network", "database-net")


@app.route("/", methods=["GET", "POST"])
def query_form():
    results = None
    error = None
    combined_containers = None

    # Get containers on the network and Docker in Docker containers
    network_containers = list_containers_on_network(Network)
    dind_containers = list_dind_containers()

    if request.method == "POST":
        # Handle container combination
        selected_network_container = request.form.get("network_container")
        selected_dind_container = request.form.get("dind_container")

        if selected_network_container and selected_dind_container:
            combined_containers = {
                "network_container": selected_network_container,
                "dind_container": selected_dind_container
            }

        # Handle the SPARQL query if present
        sparql_query = request.form.get("query")
        if sparql_query:
            sparql = SPARQLWrapper(SPARQL_ENDPOINT)
            sparql.setQuery(sparql_query)
            sparql.setReturnFormat(JSON)
            try:
                query_result = sparql.queryAndConvert()
                results = json.dumps(query_result, indent=2)
            except Exception as e:
                error = str(e)

    # Pass all the data to the template
    return render_template(
        "query_form.html",
        results=results,
        error=error,
        network_containers=network_containers,
        dind_containers=dind_containers,
        combined_containers=combined_containers
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
