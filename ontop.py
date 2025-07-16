import os
import uuid
from sqlalchemy import create_engine, Column, Integer, String, LargeBinary, Table, MetaData
import docker
import textwrap
import shutil

from SQLiteDB import SQLiteDB
DOCKER_CLIENT = os.environ.get("DOCKER_CLIENT", "unix://var/run/docker.sock") #the outside docker host
# Host paths (bind-mounted Docker volume)
HOST_INPUT_PATH = "/var/lib/docker/volumes/volume_python/_data/ontop_input"
HOST_JDBC_PATH = "/var/lib/docker/volumes/volume_python/_data/ontop_jdbc"
INPUT_PATH = "/volume/ontop_input"
JDBC_PATH = "/volume/ontop_jdbc"

JDBC_JAR_SOURCE = "./jdbc/driver.jar"
JDBC_JAR_DEST = os.path.join(JDBC_PATH, "driver.jar")

def save_deployment_files(obda_data, owl_data, properties_data, jdbc_data):
    with open("/volume/ontop_input/mappings.ttl", "wb") as f:
        f.write(obda_data)
    with open("/volume/ontop_input/ontologie.owl", "wb") as f:
        f.write(owl_data)
    with open("/volume/ontop_input/database.properties", "wb") as f:
        f.write(properties_data)
    with open("/volume/ontop_jdbc/driver.jar", "wb") as f:
        f.write(jdbc_data)

def init_directories():
    # Ensure required directories exist
    shutil.rmtree(HOST_INPUT_PATH, ignore_errors=True)

    os.makedirs(HOST_INPUT_PATH, exist_ok=True)
    os.makedirs(HOST_JDBC_PATH, exist_ok=True)

    os.makedirs(JDBC_PATH, exist_ok=True)
    os.makedirs(INPUT_PATH, exist_ok=True)

def deploy_ontop_container(obda_data, owl_data, properties_data, jdbc_data):
    save_deployment_files(obda_data, owl_data, properties_data, jdbc_data)

    client = docker.DockerClient(base_url=DOCKER_CLIENT)

    init_directories()
    random_name = f"ontop{uuid.uuid4().hex[:8]}"


    container = client.containers.run(
        image="ontop/ontop",
        detach=True,
        name =random_name,
        network="relay_db_network",
        volumes={
            HOST_INPUT_PATH: {"bind": "/opt/ontop/input", "mode": "rw"},
            HOST_JDBC_PATH: {"bind": "/opt/ontop/jdbc", "mode": "rw"},
        },
        environment={
            "ONTOP_MAPPING_FILE": "/opt/ontop/input/mappings.ttl",
            "ONTOP_ONTOLOGY_FILE": "/opt/ontop/input/ontologie.owl",
            "ONTOP_PROPERTIES_FILE": "/opt/ontop/input/database.properties",
        },
        extra_hosts={"host.docker.internal": "host-gateway"}
    )

    print(f"Ontop container started with ID {container.short_id}")
    return container.name


