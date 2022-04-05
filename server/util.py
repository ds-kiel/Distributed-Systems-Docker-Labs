# coding=utf-8
import requests
from threading import Thread
import time

def do_parallel_task(method, args=None, delay=None):
    # create a thread running a new task with optional delay
    # Usage example: self.do_parallel_task(self.contact_another_server, args=("10.1.0.2", "/index", "POST", data))
    # this would start a thread sending a post request to server 10.1.0.2 with URI /index and with params data

    def delayed():
        if delay is not None and delay >= 0:
            time.sleep(delay) # in sec
        method(*args)

    thread = Thread(target=delayed)
    thread.daemon = True
    thread.start()

def contact_another_server(srv_ip, URI, req='POST', data=None):
    # Try to contact another serverthrough a POST or GET
    # usage: server.contact_another_server("10.1.1.1", "/index", "POST", data)
    success = False
    try:
        if 'POST' in req:
            # We handle data string as json for now
            headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
            res = requests.post('http://{}{}'.format(srv_ip, URI), data=data, headers=headers)
        elif 'GET' in req:
            headers = {'Accept': 'application/json'}
            res = requests.get('http://{}{}'.format(srv_ip, URI), headers=headers)
            # result can be accessed res.json()
        if res.status_code == 200:
            success = True
    except Exception as e:
        print("[ERROR] "+str(e))
    return (success, res)


def propagate_to_all_servers(server_list, exclude_ip, URI, req='POST', data=None):
    for srv_ip in server_list:
        if srv_ip != exclude_ip:
            (success, _) = contact_another_server(srv_ip, URI, req, data)
            if not success:
                print("[WARNING ]Could not contact server {}".format(srv_ip))
           