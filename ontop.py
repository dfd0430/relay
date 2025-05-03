import os
import uuid
from sqlalchemy import create_engine, Column, Integer, String, LargeBinary, Table, MetaData
import docker
import textwrap
import shutil

from SQLiteDB import SQLiteDB

# Host paths (bind-mounted Docker volume)
HOST_INPUT_PATH = "/var/lib/docker/volumes/volume_python/_data/ontop_input"
HOST_JDBC_PATH = "/var/lib/docker/volumes/volume_python/_data/ontop_jdbc"
INPUT_PATH = "/volume/ontop_input"
JDBC_PATH = "/volume/ontop_jdbc"
# Source JDBC JAR on your host filesystem (adjust if needed)
JDBC_JAR_SOURCE = "./jdbc/driver.jar"
JDBC_JAR_DEST = os.path.join(JDBC_PATH, "driver.jar")


def write_input_files_to_host(obda_content,owl_content,properties_content):
    # Ensure required directories exist
    shutil.rmtree(HOST_INPUT_PATH, ignore_errors=True)

    os.makedirs(HOST_INPUT_PATH, exist_ok=True)
    os.makedirs(HOST_JDBC_PATH, exist_ok=True)

    os.makedirs(JDBC_PATH, exist_ok=True)
    os.makedirs(INPUT_PATH, exist_ok=True)

def deploy_ontop_container(obda_content,owl_content,properties_content):
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')

    # Stop and remove any existing container
    try:
        client.containers.get("ontoptest").remove(force=True)
    except docker.errors.NotFound:
        pass

    # Prepare files
    write_input_files_to_host(obda_content,owl_content,properties_content)

    random_name = f"ontop{uuid.uuid4().hex[:8]}"


    container = client.containers.run(
        image="ontop/ontop",
        detach=True,
        name =random_name,
        auto_remove=True,
        network="database-net",
        volumes={
            HOST_INPUT_PATH: {"bind": "/opt/ontop/input", "mode": "rw"},
            HOST_JDBC_PATH: {"bind": "/opt/ontop/jdbc", "mode": "rw"},
        },
        environment={
            "ONTOP_MAPPING_FILE": "/opt/ontop/input/mappings.obda",
            "ONTOP_ONTOLOGY_FILE": "/opt/ontop/input/ontologie.owl",
            "ONTOP_PROPERTIES_FILE": "/opt/ontop/input/database.properties",
        },
        extra_hosts={"host.docker.internal": "host-gateway"}
    )

    print(f"Ontop container started with ID {container.short_id}")
    return container.name


