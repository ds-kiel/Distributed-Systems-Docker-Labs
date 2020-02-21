from bottle import route, run, static_file
import os

num_servers = int(os.getenv('NUM_SERVERS'))
from_port = int(os.getenv('FROM_PORT'))
to_port = os.getenv('TO_PORT')


@route('/')
@route('/server/<server>')
def index(server=1):
    with open('src/index.html') as f:
        s = f.read()
        s = s.replace("%NUM_SERVERS%", str(num_servers))
        s = s.replace("%FROM_PORT%", str(from_port))

        if server is not None:
            s = s.replace("%SERVER_ID%", str(server))

        return s

@route('/<filename:path>')
def serve_static_file(filename):
    return static_file(filename, root='./src/')

run(host='0.0.0.0', port=80, debug=True)
# TODO: USe reloader?