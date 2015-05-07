"""
    Flask-RestMedia
"""
import json

from flask import abort, request
from flask.views import MethodView
from werkzeug import secure_filename


class RestMediaApi(MethodView):

    def __init__(self, restmedia):
        self.restmedia = restmedia
        self.storage = restmedia.storage

    def _secure_path(self, path):
        return path.replace('../', '')

    def get(self, path_arg=''):
        path = self._secure_path(path_arg)

        if not self.restmedia.right_callback('read', path):
            abort(403)

        r = self.storage.read(path, self.restmedia.list_dir_callback)

        if not r:
            abort(404)

        return r

    def post(self, path_arg=''):
        data = request.get_json()
        path = self._secure_path(path_arg)


        if data:
            file = None
            filename = data.get('filename')
        else:
            file = request.files['file']
            filename = secure_filename(file.filename)

        if not self.restmedia.right_callback('create', path, filename, file):
            abort(403)

        if self.storage.create(path, filename, file):
            return self.restmedia.url + path_arg + filename

        abort(400)

    def delete(self, path_arg=''):
        path = self._secure_path(path_arg)

        if not self.restmedia.right_callback('delete', path):
            abort(403)

        if self.storage.delete(path):
            return path

        abort(404)


def default_has_right(action, path, filename=None, file=None):
    """
        Default callback function for right checking, return True for all.

        :param action: read, write or delete
        :param path: path of the targeted element
        :param filename: for creation, name of the created element
        :param file: for file creation, file object
    """
    return True

def default_list_dir(path, folders, files):
    """
        Default callback function for formating directory listing

        :param path: current path
        :param folders: list of sub-folders
        :param files: list of files

        Return the list of name json encoded
    """
    return json.dumps(folders + files)

class RestMedia():
    """
        You need to initialize it with a Flask Application: ::

        >>> app = Flask(__name__)
        >>> restmedia = RestMedia(app)

        Alternatively, you can use :meth:`init_app` to set the Flask
        application after it has been constructed.

        :param app: the Flask application object
        :param media_url: Route used, default to /media/
        :param list_dir_callback: Callback used to format directory listing
            :func:`default_list_dir`
        :param right_callback: Callback used to validate right, default to
            :func:`default_has_right`
        :param storage: Storage backend : :class:`FileStorage`,
            :class:`RedisStorage` or class
            implementing :class:`RestMediaStorage`
    """
    def __init__(self, app=None, media_url='/media/',
                 list_dir_callback=default_list_dir,
                 right_callback=default_has_right, storage=None):

        self.app = app
        self.url = media_url
        self.list_dir_callback = list_dir_callback
        self.right_callback = right_callback
        self.storage = storage

        if app:
            self.init_app(app)

    def init_app(self, app):
        """
            Initialize this class with the given :class:`flask.Flask`
            application.
            :param app: the Flask application

            Examples: ::

            >>> restmedia = RestMedia()
            >>> restmedia.init_app(app)
        """
        media_view = RestMediaApi.as_view('mediaview', self)
        app.add_url_rule(self.url + '<path:path_arg>', view_func=media_view)
        app.add_url_rule(self.url, view_func=media_view)
