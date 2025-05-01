import os
import docker
import textwrap
import shutil
# Host paths (bind-mounted Docker volume)
HOST_INPUT_PATH = "/var/lib/docker/volumes/volume_python/_data/ontop_input"
HOST_JDBC_PATH = "/var/lib/docker/volumes/volume_python/_data/ontop_jdbc"
INPUT_PATH = "/volume/ontop_input"
JDBC_PATH = "/volume/ontop_jdbc"
# Source JDBC JAR on your host filesystem (adjust if needed)
JDBC_JAR_SOURCE = "./jdbc/postgresql-42.2.14.jre7.jar"
JDBC_JAR_DEST = os.path.join(JDBC_PATH, "postgresql-42.2.14.jre7.jar")


def write_input_files_to_host(obda_content,owl_content,properties_content):
    # Ensure required directories exist
    shutil.rmtree(HOST_INPUT_PATH, ignore_errors=True)

    os.makedirs(HOST_INPUT_PATH, exist_ok=True)
    os.makedirs(HOST_JDBC_PATH, exist_ok=True)

    os.makedirs(JDBC_PATH, exist_ok=True)
    os.makedirs(INPUT_PATH, exist_ok=True)

    # Copy JDBC JAR to the host-mounted JDBC path
    with open(JDBC_JAR_SOURCE, "rb") as src, open(JDBC_JAR_DEST, "wb") as dst:
        dst.write(src.read())

    # OBDA content
#     obda_content = '''[PrefixDeclaration]
# :		http://example.org/ontology#
# ex:		http://example.org/ontology#
# owl:		http://www.w3.org/2002/07/owl#
# rdf:		http://www.w3.org/1999/02/22-rdf-syntax-ns#
# xml:		http://www.w3.org/XML/1998/namespace
# xsd:		http://www.w3.org/2001/XMLSchema#
# obda:		https://w3id.org/obda/vocabulary#
# rdfs:		http://www.w3.org/2000/01/rdf-schema#
#
# [MappingDeclaration] @collection [[
# mappingId	MAPID-a72f8c68030143cbae5696153690cad6
# target		:Person/{id} a :Person ; :id {id}^^xsd:integer ; :name {name}^^xsd:string ; :age {age}^^xsd:integer .
# source		SELECT * FROM "person";
# ]]
# '''
#
#     # OWL ontology content
#     owl_content = '''@prefix ex: <http://example.org/ontology#> .
# @prefix owl: <http://www.w3.org/2002/07/owl#> .
# @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
# @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
# @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
#
# ex:Ontology a owl:Ontology ;
#     rdfs:comment "OWL ontology for a PostgreSQL table named Person, which contains id, name, and age attributes." ;
#     owl:versionInfo "1.0" .
#
# ex:age a owl:DatatypeProperty ;
#     rdfs:domain ex:Person ;
#     rdfs:range xsd:integer ;
#     rdfs:label "age" .
#
# ex:id a owl:DatatypeProperty ;
#     rdfs:domain ex:Person ;
#     rdfs:range xsd:integer ;
#     rdfs:label "id" .
#
# ex:name a owl:DatatypeProperty ;
#     rdfs:domain ex:Person ;
#     rdfs:range xsd:string ;
#     rdfs:label "name" .
#
# ex:Person a owl:Class ;
#     rdfs:label "Person" .
# '''
#
#     # Properties content
#     properties_content = textwrap.dedent("""\
#         jdbc.password=password
#         jdbc.user=postgres
#         jdbc.url=jdbc:postgresql://host.docker.internal:5433/postgres
#         jdbc.driver=org.postgresql.Driver
#     """)

    # Write files
    # with open(os.path.join("/volume/ontop_input", "mappings.obda"), "w") as f:
    #     f.write(obda_content)
    # with open(os.path.join("/volume/ontop_input", "ontologie.owl"), "w") as f:
    #     f.write(owl_content)
    # with open(os.path.join("/volume/ontop_input", "database.properties"), "w") as f:
    #     f.write(properties_content)


def deploy_ontop_container(obda_content,owl_content,properties_content):
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')

    # Stop and remove any existing container
    try:
        client.containers.get("ontoptest").remove(force=True)
    except docker.errors.NotFound:
        pass

    # Prepare files
    write_input_files_to_host(obda_content,owl_content,properties_content)

    # Start Ontop container
    container = client.containers.run(
        image="ontop/ontop",
        name="ontoptest",
        detach=True,
        network="database-net",
        ports={"8080/tcp": 8089},
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




