# coding=utf-8

import argparse
import json
import sys
import socket
import os
import dns.resolver,dns.reversename
from bottle import Bottle, request, run
from server import BlackboardServer


print(sys.argv[1])
num_servers = int(os.getenv('NUM_SERVERS'))
from_port = int(os.getenv('FROM_PORT'))
to_port = os.getenv('TO_PORT')

p_ip = socket.gethostbyname(socket.gethostname())
print (dns.resolver.query(dns.reversename.from_address(p_ip),"PTR"))
print (str(dns.resolver.query(dns.reversename.from_address(p_ip),"PTR")[0]))





try:
    server = BlackboardServer(own_id,
                    own_ip,
                    server_list)
    run(server,
                host=own_ip,
                port=args.port)
except Exception as e:
    print("[ERROR] "+str(e))