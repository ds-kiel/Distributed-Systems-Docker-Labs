from bottle import route, run, static_file
import os

SERVER_LIST = os.getenv('SERVER_LIST')

@route('/')
@route('/server/<server>')
def index(server=1):
    with open('src/index.html') as f:
        s = f.read()
        return s.replace("%SERVER_LIST%", SERVER_LIST).replace("%SERVER_ID%", str(server))

@route('/<filename:path>')
def serve_static_file(filename):
    return static_file(filename, root='./src/')

run(host='0.0.0.0', port=80, debug=False, server='paste')
# TODO: USe reloader?