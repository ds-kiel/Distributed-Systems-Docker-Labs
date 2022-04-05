from bottle import route, run, static_file
import os

SERVER_LIST = os.getenv('SERVER_LIST')
GROUP_NAME = os.getenv('GROUP_NAME')

@route('/')
@route('/server/<server>')
def index(server=1):
    with open('src/index.html') as f:
        s = f.read()
        s = s.replace("%SERVER_LIST%", SERVER_LIST).replace("%SERVER_ID%", str(server))
        s = s.replace("%GROUP_NAME%", GROUP_NAME)
        return s

@route('/<filename:path>')
def serve_static_file(filename):
    return static_file(filename, root='./src/')

run(host='0.0.0.0', port=80, debug=False, server='paste')
# TODO: Use reloader?