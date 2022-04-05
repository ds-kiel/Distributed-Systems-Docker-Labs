import docker
import sys
import os
import argparse
import requests
import time
from dotenv import load_dotenv
import itertools
import threading
import json

load_dotenv()

FRONTEND_PORT=int(os.getenv('FRONTEND_PORT'))
BASE_SERVER_PORT=int(os.getenv('BASE_SERVER_PORT'))
PROXY_PORT=int(os.getenv('PROXY_PORT'))
GROUP_NAME=str(os.getenv('GROUP_NAME'))
DOCKER_LABEL=str(os.getenv('DOCKER_LABEL'))
FRONTEND_IMAGE=str(os.getenv('FRONTEND_IMAGE'))
SERVER_IMAGE=str(os.getenv('SERVER_IMAGE'))

num_servers = int(sys.argv[1]) if len(sys.argv) > 1  else 1

PROXY_IMAGE = 'shopify/toxiproxy'

client = docker.from_env()

def attach_logs(container):
    def _print(name, stream):
        for line in stream:
            print(name +": " + line.decode('utf8').strip())
    t = threading.Thread(target=_print, args=(container.name, container.attach(logs=True,stream=True)))
    t.daemon = True
    t.start()


# Remove any running container instances
def remove():
    # Remove frontend, proxy and individual servers
    try:
        containers = client.containers.list(filters={"label": DOCKER_LABEL}, all=True)
        for container in containers:
            container.remove(force=True)
    except Exception as e:
        print(e)
        pass

    # Remove the network
    try:
        nets = client.networks.list(names=[DOCKER_LABEL + "_net"])
        for net in nets:
            net.remove()
    except Exception as e:
        print(e)
        pass

remove()

# Add the network

network = client.networks.create(DOCKER_LABEL + "_net", driver="bridge")

proxy_ports = {
    '8474': str(PROXY_PORT)
}

internal_server_list=[]
external_server_list=[]
for server_port in range(BASE_SERVER_PORT, BASE_SERVER_PORT+num_servers):
    proxy_ports[str(server_port)] = str(server_port)
    internal_server_list.append("proxy:"+str(server_port))
    external_server_list.append("localhost:"+str(server_port))

internal_server_list = ",".join(internal_server_list)
external_server_list = ",".join(external_server_list)

proxy_container = client.containers.run(PROXY_IMAGE,
                                        detach=True,
                                        labels={DOCKER_LABEL: 'proxy'},
                                        name=DOCKER_LABEL+'_proxy',
                                        hostname='proxy',
                                        ports=proxy_ports,
                                        environment = {
                                            "LOG_LEVEL": "error"
                                        }
                                    )
attach_logs(proxy_container)


network.connect(proxy_container, aliases=['proxy'])

frontend_container = client.containers.run(FRONTEND_IMAGE,
                            detach=True,
                            labels={DOCKER_LABEL: 'frontend'},
                            name=DOCKER_LABEL+'_frontend',
                            hostname='frontend',
                            ports={'80': FRONTEND_PORT},
                            environment = {
                                "SERVER_LIST": external_server_list,
                                "GROUP_NAME": GROUP_NAME
                            }
                        )
attach_logs(frontend_container)

server_containers = []

for server_id in range(1, num_servers+1):
    server_name = "server_{}".format(server_id)
    server_container = client.containers.run(SERVER_IMAGE,
                                        detach=True,
                                        labels={DOCKER_LABEL: 'server'},
                                        name=DOCKER_LABEL+ '_' + server_name,
                                        hostname=server_name,
                                        environment = {
                                            "SERVER_LIST": internal_server_list,
                                            "SERVER_ID": server_id
                                        }
                                        )
    attach_logs(server_container)
    server_containers.append(server_container)
    network.connect(server_container, aliases=[server_name])


for server_id in range(1, num_servers+1):
    server_name = "server_{}".format(server_id)
    data = {'listen':"0.0.0.0:" + str(BASE_SERVER_PORT + (server_id-1)), 'upstream': server_name + ":80", 'name': server_name}
    ret = requests.post('http://0.0.0.0:' + str(PROXY_PORT) + '/proxies', data=json.dumps(data).encode("utf-8"))

print("CTRL-C to shutdown...")


# Some scenarios TODO

def scenario_clear():
    pass

def scenario_half_split():
    pass

def scenario_request_loss(p=0.1):
    pass

try:
    # TODO: We could execute specific scenarios if wanted, e.g. post some entries to the servers, change the network topology using toxiproxy etc.
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    pass


print("Shutting down...")
remove()
print("Finished")