# coding=utf-8
from bottle import Bottle, request, HTTPError
import util


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
        self.patch('/entries/<entry_id:int>', callback=self.update_entry_request)

        # if you add new URIs to the server, you need to add them here
        # You can have variables in the URI, here's an example
        # self.post('/propagate/<entry_id:int>/', callback=self.propagate_entry) where post_board takes an argument (integer) called entry_id

    def list_entries_request(self):
        entries = self.blackboard.entries
        return map(lambda entry: entry.to_dict(), entries)

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