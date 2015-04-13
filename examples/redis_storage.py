from flask import Flask

from flask_restmedia import RestMedia
from flask_restmedia.storages import RedisStorage

def has_right(action, path, filename=None, file=None):
    print 'Asking for right {action} on {path}/{filename}'.format(
          action=action, path=path, filename=filename)

    return True

app = Flask(__name__)
app.debug = True
restmedia = RestMedia(app, right_callback=has_right, storage=RedisStorage())
print 'Redis backend on {url}'.format(url=restmedia.url)
app.run()
