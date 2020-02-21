from toxiproxy.api import validate_response
import requests
import os
from toxiproxy import Toxiproxy

num_servers = int(os.getenv('NUM_SERVERS'))
from_port = int(os.getenv('FROM_PORT'))
to_port = os.getenv('TO_PORT')



tp = Toxiproxy()
tp.update_api_consumer('proxy', '8474')


proxies = dict()

print("ASD")
print(num_servers)

def get_server_name(id):
    return server_base_name + str(id)


def init_proxy(server_id):
    print("INIT PROXY" + str(server_id))
    server_name = "labs_server_{}".format(server_id)
    proxy = tp.create(listen="0.0.0.0:" + str(from_port + (server_id-1)), upstream=server_name + ":80", name=server_name)

for i in range(1, num_servers+1):
    print(i)
    init_proxy(i)
