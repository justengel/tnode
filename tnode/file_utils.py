class FileWrapper:
    def __init__(self, filename, mode='r', *args, **kwargs):
        self._fp = None
        self.filename = filename
        self.mode = mode
        self.args = args
        self.kwargs = kwargs

    @property
    def fp(self):
        if self._fp is None:
            return self.filename
        return self._fp

    @fp.setter
    def fp(self, value):
        self._fp = value

    @property
    def name(self):
        try:
            return self.fp.name
        except (AttributeError, Exception):
            if isinstance(self.filename, str):
                return self.filename
            raise AttributeError('Unknown "name"!')

    @staticmethod
    def format_read(val, mode):
        try:
            if not isinstance(val, str) and 'b' not in self.mode:
                return val.decode('utf-8')
            elif isinstance(val, str) and 'b' in self.mode:
                return val.encode('utf-8')
        except (AttributeError, TypeError, Exception):
            pass
        return val

    def read(self, size=-1):
        """Read at most size bytes from the file (less if the read hits EOF before obtaining size bytes). If the size
        argument is negative or omitted, read all data until EOF is reached. The bytes are returned as a string object.
        An empty string is returned when EOF is encountered immediately. (For certain files, like ttys, it makes sense
        to continue reading after an EOF is hit.) Note that this method may call the underlying C function fread() more
        than once in an effort to acquire as close to size bytes as possible. Also note that when in non-blocking mode,
        less data than what was requested may be returned, even if no size parameter was given.
        """
        return self.format_read(self.fp.read(size), self.mode)

    def __next__(self):
        try:
            return self.format_read(self.fp.__next__(), self.mode)
        except (AttributeError, ValueError, TypeError, Exception):
            raise StopIteration

    def __iter__(self):
        return self

    def __enter__(self):
        try:
            if self._fp is None:
                self._fp = open(self.filename, self.mode, *self.args, **self.kwargs)
        except TypeError:
            pass
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self._fp.close()
        except (AttributeError, TypeError, ValueError, Exception):
            pass
        return exc_type is None
