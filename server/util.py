# coding=utf-8
import requests
from threading import Thread
import time

def _wrapper_delay_and_execute(delay, method, args):
    time.sleep(delay) # in sec
    method(*args)


def do_parallel_task(method, args=None, delay=None):
    # create a thread running a new task with optional delay
    # Usage example: self.do_parallel_task(self.contact_another_server, args=("10.1.0.2", "/index", "POST", params_dict))
    # this would start a thread sending a post request to server 10.1.0.2 with URI /index and with params params_dict

    if delay is not None and delay >= 0:
        thread = Thread(target=method,
                    args=args)
    else:
        thread = Thread(target=_wrapper_delay_and_execute, args=(delay, method, args))

    thread.daemon = True
    thread.start()


def contact_another_server(srv_ip, URI, req='POST', params_dict=None):
    # Try to contact another serverthrough a POST or GET
    # usage: server.contact_another_server("10.1.1.1", "/index", "POST", params_dict)
    success = False
    try:
        if 'POST' in req:
            res = requests.post('http://{}{}'.format(srv_ip, URI),
                                data=params_dict)
        elif 'GET' in req:
            res = requests.get('http://{}{}'.format(srv_ip, URI))
        # result can be accessed res.json()
        if res.status_code == 200:
            success = True
    except Exception as e:
        print("[ERROR] "+str(e))
    return success


def propagate_to_all_servers(server_list, exclude_ip, URI, req='POST', params_dict=None):
    for srv_ip in server_list:
        if srv_ip != exclude_ip:
            success = contact_another_server(srv_ip, URI, req, params_dict)
            if not success:
                print("[WARNING ]Could not contact server {}".format(srv_ip))
           