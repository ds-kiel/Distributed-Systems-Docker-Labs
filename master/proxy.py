
from toxiproxy import Toxiproxy


tp = Toxiproxy()
tp.update_api_consumer('localhost', '8474')

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
