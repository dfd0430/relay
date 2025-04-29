import docker
from docker.tls import TLSConfig
from datetime import datetime
import json
import io
import tarfile

IP_LOG_FILE = "ip_log.txt"
DOCKER_HOST = "tcp://pht-dind:2376"
CLIENT_CERT = "/certs/cert.pem"
CLIENT_KEY = "/certs/key.pem"
FLASK_SERVER_ADDRESS = "137.226.58.20:8082"

def get_container_name_by_ip(ip):


    tls_config = TLSConfig(client_cert=(CLIENT_CERT, CLIENT_KEY), verify=False)

    try:
        docker_client = docker.DockerClient(base_url=DOCKER_HOST, tls=tls_config)
        containers = docker_client.containers.list()
        for container in containers:
            container_inspect = container.attrs
            networks = container_inspect.get("NetworkSettings", {}).get("Networks", {})
            with open(IP_LOG_FILE, "a") as log_file:
                log_file.write(f"container inspect result: {networks}\n")

            for network in networks.values():
                if network.get("IPAddress") == ip:
                    container_name = container.name
                    with open(IP_LOG_FILE, "a") as log_file:
                        log_file.write(
                            f"{datetime.now()} - IP: {ip} - Container: {container_name}\n"
                        )
                    return container_name

    except Exception as e:
        error_message = f"Error resolving container: {str(e)}"
        return error_message

    with open(IP_LOG_FILE, "a") as log_file:
        log_file.write(f"{datetime.now()} - IP: {ip} - Container: Unknown\n")

    return "Unknown"

def list_containers_on_network(network_name):
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')

    container_list = []

    try:
        network = client.networks.get(network_name)
        containers = network.attrs['Containers']

        for container_id, details in containers.items():
            container_info = {
                "id": container_id,
                "name": details["Name"],
                "ipv4_address": details.get("IPv4Address", "").split('/')[0],  # Strip subnet
                "mac_address": details.get("MacAddress", "")
            }
            container_list.append(container_info)

        return container_list
        #names = [c['name'] for c in containers]

    except docker.errors.NotFound:
        print(f"Network '{network_name}' not found.")
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []

def list_dind_containers():

    tls_config = TLSConfig(client_cert=(CLIENT_CERT, CLIENT_KEY), verify=False)

    try:
        docker_client = docker.DockerClient(base_url=DOCKER_HOST, tls=tls_config)
        containers = docker_client.containers.list()

        container_list = []

        for container in containers:
            container_inspect = container.attrs
            container_info = {
                "id": container.short_id,
                "name": container.name,
                "networks": {}
            }

            networks = container_inspect.get("NetworkSettings", {}).get("Networks", {})
            for net_name, net_details in networks.items():
                container_info["networks"][net_name] = net_details.get("IPAddress")

            container_list.append(container_info)

            # Optional logging
            with open(IP_LOG_FILE, "a") as log_file:
                log_file.write(
                    f"{datetime.now()} - Container: {container.name}, Networks: {container_info['networks']}\n"
                )

        return container_list
        # names = [container['name'] for container in containers]
        # print(names)

    except Exception as e:
        error_message = f"Error listing containers: {str(e)}"
        with open(IP_LOG_FILE, "a") as log_file:
            log_file.write(f"{datetime.now()} - {error_message}\n")
        return {"error": error_message}


def find_network_container(dind_name, filename='combined_containers.json'):
    with open(filename, 'r') as file:
        data = json.load(file)

    for item in data:
        if item['dind_container'] == dind_name:
            return item['network_container']

    return None




def setup_nginx():
    tls_config = TLSConfig(
        client_cert=(CLIENT_CERT, CLIENT_KEY),
        verify=False
    )

    client = docker.DockerClient(base_url=DOCKER_HOST, tls=tls_config)

    # Define nginx.conf
    nginx_conf = f"""
events {{}}

http {{
    server {{
        listen 80;
        location / {{
            proxy_pass http://{FLASK_SERVER_ADDRESS};
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }}
    }}
}}
"""

    # Define Dockerfile
    dockerfile = """
FROM nginx:latest
COPY nginx.conf /etc/nginx/nginx.conf
"""

    # Create in-memory tar archive with Dockerfile and nginx.conf
    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode='w') as tar:
        # Add Dockerfile
        dockerfile_bytes = dockerfile.strip().encode('utf-8')
        dockerfile_info = tarfile.TarInfo(name='Dockerfile')
        dockerfile_info.size = len(dockerfile_bytes)
        tar.addfile(dockerfile_info, io.BytesIO(dockerfile_bytes))

        # Add nginx.conf
        nginx_conf_bytes = nginx_conf.strip().encode('utf-8')
        nginx_conf_info = tarfile.TarInfo(name='nginx.conf')
        nginx_conf_info.size = len(nginx_conf_bytes)
        tar.addfile(nginx_conf_info, io.BytesIO(nginx_conf_bytes))

    tar_stream.seek(0)  # Rewind the stream to the beginning

    try:
        # Build image from in-memory tar
        image, build_logs = client.images.build(
            fileobj=tar_stream,
            custom_context=True,
            tag="custom-nginx-proxy",
            rm=True,
            pull=True
        )

        # Remove old container if it exists
        try:
            old_container = client.containers.get("nginx-proxy")
            old_container.remove(force=True)
        except docker.errors.NotFound:
            pass

        # Run the nginx container
        container = client.containers.run(
            "custom-nginx-proxy",
            name="nginx-proxy",
            detach=True,
            network_mode="host",
            auto_remove=True  # Container auto-deletes on exit
        )

        print(f"NGINX container {container.id} started successfully")
        return True

    except docker.errors.APIError as e:
        print(f"Failed to start nginx container: {str(e)}")
        raise e



