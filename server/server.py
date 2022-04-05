# coding=utf-8
from bottle import Bottle, request, HTTPError, run, response
import util
import os
import time
import json

# A simple entry in our blackboard
class Entry:
    def __init__(self, text):
        self.text = text
    
    def to_dict(self):
        return {
            "text": self.text
        }
    
    def from_dict(data):
        return Entry(data['text'])

    def __str__(self):
        return str(self.to_dict())

# ------------------------------------------------------------------------------------------------------
# You need to synchronize the access to the board once you enable multithreading in the server (e.g. using a Lock)
class Blackboard():

    def __init__(self):
        self.entries = []

    def get_entries(self):
        return self.entries

    def add_entry(self, entry):
        self.entries.append(entry)


# ------------------------------------------------------------------------------------------------------
class BlackboardServer(Bottle):

    def __init__(self, ID, IP, server_list):
        super(BlackboardServer, self).__init__()
        self.blackboard = Blackboard()
        self.id = int(ID)
        self.ip = str(IP)
        self.server_list = server_list

        # Handle CORS
        self.route('/<:re:.*>', method='OPTIONS', callback=self.add_cors_headers)
        self.add_hook('after_request', self.add_cors_headers)

        # Define REST URIs for the frontend
        self.get('/entries', callback=self.list_entries_request)
        self.post('/entries', callback=self.create_entry_request)
        self.delete('/entries', callback=self.delete_entry_request)  
        
        # if you add new URIs to the server, you need to add them here
        # You can have variables in the URI, here's an example
        self.post('/dummy_propagation', callback=self.dummy_propagation)

    def add_cors_headers(self):
        """
        You need to add some headers to each request.
        Don't use the wildcard '*' for Access-Control-Allow-Origin in production.
        """
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'PUT, GET, POST, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

    def list_entries_request(self):
        entries = self.blackboard.entries
        return {
            "entries": list(map(lambda entry: entry.to_dict(), entries))
        }

    def create_entry_request(self):
        try:
            entry_text = request.forms.get('text')
            entry = Entry(entry_text)
            self.blackboard.add_entry(entry)
            print("Received: {}".format(entry))
            # You could now propagate that to all servers, like this:
            #util.propagate_to_all_servers(self.server_list, self.ip, '/dummy_propagation', 'POST', json.dumps(entry.to_dict()))
            #print("Propagated: {}".format(entry))
            # Or a delayed version:
            #util.do_parallel_task(util.propagate_to_all_servers, args=(self.server_list, self.ip, '/dummy_propagation', 'POST', json.dumps(entry.to_dict())), delay=10)
        except Exception as e:
            print("[ERROR] "+str(e))
            raise e

    def dummy_propagation(self):
        try:
            entry = Entry.from_dict(request.json)
            print("Received: {}".format(entry))
            self.blackboard.add_entry(entry)
        except Exception as e:
            print("[ERROR] "+str(e))
            raise e


    def update_entry_request(self, entry_id):
        return HTTPError(500, "Method not implemented!")

    def delete_entry_request(self, entry_id):
        return HTTPError(500, "Method not implemented!")

# Sleep a bit to allow logging to be attached
time.sleep(2)

server_list = os.getenv('SERVER_LIST').split(',')
own_id = int(os.getenv('SERVER_ID'))
own_ip = server_list[own_id-1]
server = BlackboardServer(own_id, own_ip, server_list)

print("#### Starting BlackboardServer " + str(own_id))
run(server, host='0.0.0.0', port=80, debug=True)