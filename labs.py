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
import uuid

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

external_server_list = []

for server_port in range(BASE_SERVER_PORT, BASE_SERVER_PORT+num_servers):
    proxy_ports[str(server_port)] = str(server_port)
    external_server_list.append("localhost:"+str(server_port))

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


# A dictionary that contains the port mapping (from, to) -> port
conn_pair_ports = {}
port = BASE_SERVER_PORT + num_servers  # the first num_servers are direct proxies that we do not target

for f in range(1, num_servers+1):
    for t in range(1, num_servers+1):
        conn_pair_ports[(f,t)] = port
        port += 1


def get_server_list_str(from_server_id):
    sl = []
    for b in range(1, num_servers+1):
        sl.append("proxy:"+str(conn_pair_ports[(from_server_id, b)]))
    return ",".join(sl)

server_containers = []

for server_id in range(1, num_servers+1):
    server_name = "server_{}".format(server_id)
    server_container = client.containers.run(SERVER_IMAGE,
                                        detach=True,
                                        labels={DOCKER_LABEL: 'server'},
                                        name=DOCKER_LABEL+ '_' + server_name,
                                        hostname=server_name,
                                        environment = {
                                            "SERVER_LIST": get_server_list_str(server_id),
                                            "SERVER_ID": server_id
                                        }
                                    )
    attach_logs(server_container)
    server_containers.append(server_container)
    network.connect(server_container, aliases=[server_name])


# Create proxies

# Create external proxies as well
for server_id in range(1, num_servers+1):
    to_server_name = "server_{}".format(server_id)
    server_port = BASE_SERVER_PORT+server_id-1

    data = {'listen':"0.0.0.0:" + str(server_port), 'upstream': to_server_name + ":80", 'name': "ext_" + to_server_name }
    ret = requests.post('http://0.0.0.0:' + str(PROXY_PORT) + '/proxies', data=json.dumps(data).encode("utf-8"))

conn_pair_proxies_names = {}
conn_pair_proxies_data = {}
for (f,t) in conn_pair_ports:
    from_server_name = "server_{}".format(f)
    to_server_name = "server_{}".format(t)
    p = conn_pair_ports[(f,t)]

    name = from_server_name + "_to_" + to_server_name
    data = {'listen':"0.0.0.0:" + str(p), 'upstream': to_server_name + ":80", 'name': name }
    conn_pair_proxies_names[(f,t)] = name
    conn_pair_proxies_data[(f,t)] = data

    ret = requests.post('http://0.0.0.0:' + str(PROXY_PORT) + '/proxies', data=json.dumps(data).encode("utf-8"))


def print_proxies():
    res = requests.get('http://0.0.0.0:' + str(PROXY_PORT) + '/proxies')
    print(res.json())

# Some scenarios
def clear():
    requests.post('http://0.0.0.0:' + str(PROXY_PORT) + '/reset')

def add_half_split():
    for (f,t) in conn_pair_ports:
        # if they are not in the same "half" we disable their connections
        # note that this still allows connections to itself and symmetrically disabled (t,f)
        if (f-t) % 2 != 0:
            data = conn_pair_proxies_data[(f,t)]
            data['enabled'] = False
            requests.post('http://0.0.0.0:' + str(PROXY_PORT) + '/proxies/' + conn_pair_proxies_names[(t,f)], json=data)


def add_loss(direction='upstream', p=0.1):
    for (f,t) in conn_pair_ports:
        # if they are not in the same "half" we disable their connections
        # note that this still allows connections to itself and symmetrically disabled (t,f)
        if f != t:
            data = {
                'type': 'limit_data',
                'stream': direction,
                'toxicity': p,
                'attributes': {
                    'bytes': 0
                }
            } 
            res = requests.post('http://0.0.0.0:' + str(PROXY_PORT) + '/proxies/' + conn_pair_proxies_names[(t,f)] + '/toxics', json=data)

def add_request_loss(p=0.1):
    add_loss('upstream', p)

def add_response_loss(p=0.1):
    add_loss('downstream', p)


def add_latency(direction='upstream', delay_ms=1000, jitter_ms=500):
    for (f,t) in conn_pair_ports:
        if f != t:
            data = {
                'type': 'latency',
                'stream': direction,
                'toxicity': 1.0,
                'attributes': {
                    'latency': delay_ms,
                    'jitter': jitter_ms,
                }
            } 
            res = requests.post('http://0.0.0.0:' + str(PROXY_PORT) + '/proxies/' + conn_pair_proxies_names[(t,f)] + '/toxics', json=data)

def add_request_latency(delay_ms=1000, jitter_ms=500):
    add_latency('upstream', delay_ms, jitter_ms)

def add_response_latency(delay_ms=1000, jitter_ms=500):
    add_latency('downstream', delay_ms, jitter_ms)


def add_bandwidth(direction='upstream', rate_kb=1000):
    for (f,t) in conn_pair_ports:
        if f != t:
            data = {
                'type': 'bandwidth',
                'stream': direction,
                'toxicity': 1.0,
                'attributes': {
                    'rate': rate_kb
                }
            } 
            res = requests.post('http://0.0.0.0:' + str(PROXY_PORT) + '/proxies/' + conn_pair_proxies_names[(t,f)] + '/toxics', json=data)

def add_request_bandwidth(rate_kb=1000):
    add_bandwidth('upstream', rate_kb)

def add_response_bandwidth(rate_kb=1000):
    add_bandwidth('downstream', rate_kb)


def add_timeout(p=0.1, timeout_ms=60000):
    for (f,t) in conn_pair_ports:
        if f != t:
            data = {
                'type': 'timeout',
                'stream': 'upstream',
                'toxicity': p,
                'attributes': {
                    'timeout': timeout_ms
                }
            } 
            res = requests.post('http://0.0.0.0:' + str(PROXY_PORT) + '/proxies/' + conn_pair_proxies_names[(t,f)] + '/toxics', json=data)


# Unrealistic conditions, no loss, no timeouts, reorderings unlikely
def scenario_perfect(p=0.1):
    clear()
    
# Connections can timeout and requests do not reach their target, reorderings unlikely
def scenario_easy(p=0.1):
    scenario_perfect()

    add_timeout(p)
    add_request_loss(p)

# Connections can timeout, requests and also the response may not reach their target, reorderings unlikely
def scenario_medium(p=0.1):
    scenario_easy(p)

    add_response_loss(p)


# Connections can timeout, requests and also the response may not reach their target, messages are delayed, reorderings likely
def scenario_hard(p=0.1):
    scenario_medium(p)

    add_request_latency()
    add_response_latency()

    add_request_bandwidth()
    add_response_bandwidth()

#print_proxies()

def test_scenario(name, timeout_s=20, check_list = []):
    print("Testing scenario " + name + "...")

    for server_id in range(1, num_servers+1):
        to_server_name = "server_{}".format(server_id)
        server_port = BASE_SERVER_PORT+server_id-1
        entry_text = name + "-" + str(uuid.uuid4())
        check_list.append(entry_text)
        data = {'text': entry_text}
        ret = requests.post('http://0.0.0.0:' + str(server_port) + '/entries', data=data, headers= {'Content-type': 'application/json', 'Accept': 'application/json'})

    print("Waiting...")
    time.sleep(timeout_s)

    print("Checking consistency...")
    
    def check_content(xs,ys):
        xs = [json.dumps(x, sort_keys=True) for x in xs]
        ys = [json.dumps(y, sort_keys=True) for y in ys]

        for x in xs:
            if x not in ys:
                return False
        for y in ys:
            if y not in xs:
                return False
        return len(xs) == len(ys)
    
    def check_ordering(xs,ys):
        xs = [json.dumps(x, sort_keys=True) for x in xs]
        ys = [json.dumps(y, sort_keys=True) for y in ys]

        for i in range(min(len(xs), len(ys))):
            if xs[i] != ys[i]:
                return False
        return True

    check_entries = None

    for server_id in range(1, num_servers+1):
        to_server_name = "server_{}".format(server_id)
        server_port = BASE_SERVER_PORT+server_id-1
        data = {'text': str(server_id)}
        ret = requests.get('http://0.0.0.0:' + str(server_port) + '/entries')
        print(ret.json())
        entry_list = [x['text'] for x in ret.json()['entries']]


        if len(entry_list) != len(check_list):
            print("WARNING: Server {}: Length diff".format(server_id))

        all_entries_found = True
        for c in check_list:
            if c not in entry_list:
                all_entries_found = False

        if not all_entries_found:
            print("WARNING: Server {}: Not all entries found".format(server_id))

        # TODO: Check orderings between the different servers
    return check_list

TEST = True

print("CTRL-C to shutdown...")
try:
    if TEST:
        time.sleep(10)  # wait until the services are up

        scenario_perfect()
        check_list = test_scenario("perfect")
        
        scenario_easy()
        check_list = test_scenario("easy", check_list=check_list)

        scenario_medium()
        check_list = test_scenario("medium", check_list=check_list)

        scenario_hard()
        check_list = test_scenario("hard", check_list=check_list)
        
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    pass


print("Shutting down...")
remove()
print("Finished")