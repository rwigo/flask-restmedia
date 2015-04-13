import sys

from flask import Flask
from flask_restmedia import RestMedia
from flask_restmedia.storages import FileStorage


def has_right(action, path, filename=None, file=None):
    print 'Asking for right {action} on {path}/{filename}'.format(
          action=action, path=path, filename=filename)

    if action == 'read':
        return True

    return False

if len(sys.argv) < 2:
    print sys.argv[0] + ' <path to share>'
    exit
else:
    app = Flask(__name__)
    app.debug = True
    restmedia = RestMedia(app, right_callback=has_right,
                          storage=FileStorage(sys.argv[1]))
    print '{root} mapped read-only on {url}'.format(root=sys.argv[1],
                                                    url=restmedia.url)
    app.run()
