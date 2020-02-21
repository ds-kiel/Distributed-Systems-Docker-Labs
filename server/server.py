# coding=utf-8
from bottle import Bottle, request, HTTPError, run, response
import util
import os

# A simple entry in our blackboard
class Entry:
    def __init__(self, text):
        self.text = text
    
    def to_dict(self):
        return {
            "text": self.text
        }

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

        # Define REST URIs for the frontend
        self.get('/entries', callback=self.list_entries_request)
        self.post('/entries', callback=self.create_entry_request)
        self.delete('/entries', callback=self.delete_entry_request)
        self.route('/entries/<entry_id:int>', method='PATCH', callback=self.update_entry_request)

        # Handle CORS
        self.route('/<:re:.*>', method='OPTIONS', callback=self.add_cors_headers)
        self.add_hook('after_request', self.add_cors_headers)
        
        # if you add new URIs to the server, you need to add them here
        # You can have variables in the URI, here's an example
        # self.post('/propagate/<entry_id:int>/', callback=self.propagate_entry) where post_board takes an argument (integer) called entry_id

        self.blackboard.add_entry(Entry(str(self.id)))

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
            util.propagate_to_all_servers(self.server_list, self.ip, '/entries', 'POST', {"text": entry_text})
            print("Propagated: {}".format(entry))
        except Exception as e:
            print("[ERROR] "+str(e))
            raise e

    def update_entry_request(self, entry_id):
        return HTTPError(500, "Method not implemented!")

    def delete_entry_request(self, entry_id):
        return HTTPError(500, "Method not implemented!")

server_list = os.getenv('SERVER_LIST').split(',')
own_id = int(os.getenv('SERVER_ID'))
own_ip = server_list[own_id-1]
server = BlackboardServer(own_id, own_ip, server_list)
print("Starting BlackboardServer " + str(own_id))
run(server, host='0.0.0.0', port=80, debug=True)