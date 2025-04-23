import docker
from docker.tls import TLSConfig
from datetime import datetime

IP_LOG_FILE = "ip_log.txt"

def get_container_name_by_ip(ip):
    DOCKER_HOST = "tcp://pht-dind:2376"
    CLIENT_CERT = "/certs/cert.pem"
    CLIENT_KEY = "/certs/key.pem"

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
    DOCKER_HOST = "tcp://pht-dind:2376"
    CLIENT_CERT = "/certs/cert.pem"
    CLIENT_KEY = "/certs/key.pem"

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
