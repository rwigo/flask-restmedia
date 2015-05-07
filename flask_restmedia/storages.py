
import mimetypes
import os
import json
from flask import make_response, send_file


class RestMediaStorage():
    """
        Base class for storage backends.

    """

    def create(self, path, filename, file=None):
        """
        Handle file and path creation

        :param path: path of the created element
        :param filename: filename of the created element
        :param file: the File object if the element is a file

        Should return True in case of success.
        """
        pass

    def read(self, path):
        """
        Handle file and path reading

        :param path: path of the created element
        :param filename: filename if the element is a file
        :param file: the File object if the element is a file

        Should return a valid Flask response :
            - json array {'name': name, 'type': 'folder' or 'file'}
            - the file itself otherwise
        """
        pass

    def delete(self, path):
        """
        Handle file and path deletion

        :param path: path of the created element

        Return True in case of success.
        """
        pass


class FileStorage(RestMediaStorage):
    """
        Filesystem backend

        :param root_path: the root directory used
    """
    def __init__(self, root_path):
        self.root_path = root_path

    def create(self, path, filename=None, file=None):

        filepath = os.path.join(self.root_path, path, filename)

        if os.path.exists(filepath):
            return None

        if file:
            file.save(filepath)
        else:
            os.mkdir(filepath)

        return True

    def read(self, path, dir_list_callback):

        path = os.path.join(self.root_path, path)

        if os.path.isdir(path):
            folders = files = []
            listdir = os.listdir(path)

            for l in listdir:
                if os.path.isdir(os.path.join(path, l)):
                    folders.append(l)
                else:
                    files.append(l)

            return dir_list_callback(path, folders, files)

        elif os.path.isfile(path):
            return send_file(path)

        return None

    def delete(self, path):

        path = os.path.join(self.root_path, path)

        try:
            if os.path.isdir(path):
                os.rmdir(path)
                return True
            elif os.path.isfile(path):
                os.remove(path)
                return True
        except OSError:
            return False

        return None


class RedisStorage(RestMediaStorage):
    """
        Redis backend

        :param kwargs: arguments are forwarded to Redis() object

        See redis-py documentation for more information.
    """
    def __init__(self, **kwargs):
        try:
            from redis import Redis
        except ImportError:
            raise ImportError('You need redis-py to use RedisStorage')

        self.redis = Redis(**kwargs)
        self.rstring = "{{'type': '{type}', 'name': '{name}'}}"

    def create(self, path, filename, file=None):

        if file:
            filepath = os.path.join(path, filename)

            if self.redis.exists(filepath):
                return None

            self.redis.set(filepath, file.read())
            return self.redis.rpush(path, self.rstring.format(type='file',
                                                              name=filename))

        else:
            return self.redis.rpush(path, self.rstring.format(type='folder',
                                                              name=filename))

        return None

    def read(self, path):

        type = self.redis.type(path)

        if type == 'list':
            return json.dumps(self.redis.lrange(path, 0, -1))
        elif type == 'string':
            r = make_response(self.redis.get(path))
            r.mimetype = mimetypes.guess_type(path)[0]
            return r
        return None

    def delete(self, path):
        split = path.split('/')
        parent = '/'.join(split[:-1])
        filename = ''.join(split[-1:])

        if self.redis.type(path) == 'string':
            self.redis.lrem(parent, self.rstring.format(type='file',
                                                        name=filename))
            return self.redis.delete(path)

        elif parent:
            self.redis.lrem(parent, self.rstring.format(type='folder',
                                                        name=filename))

        return None
