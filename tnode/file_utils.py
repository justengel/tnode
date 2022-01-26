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
            if not isinstance(val, str) and 'b' not in mode:
                return val.decode('utf-8')
            elif isinstance(val, str) and 'b' in mode:
                return val.encode('utf-8')
        except (AttributeError, TypeError, Exception):
            pass
        return val

    def fileno(self):
        """Return the integer ``file descriptor'' that is used by the underlying implementation to request I/O
        operations from the operating system. This can be useful for other, lower level interfaces that use file
        descriptors, such as the fcntl module or os.read() and friends. Note: File-like objects which do not have
        a real file descriptor should not provide this method!
        """
        try:
            return self.fp.fileno()
        except (AttributeError, Exception):
            return -1

    def writable(self):
        """Return if the file is writable."""
        try:
            return self.fp.writable()
        except (AttributeError, Exception):
            return False

    def write(self, msg):
        """Write the given bytes to the buffer or file."""
        msg = self.format_read(msg, self.mode)
        return self.fp.write(msg)

    def readable(self):
        """Return if the file is readable."""
        try:
            return self.fp.readable()
        except (AttributeError, Exception):
            return False

    def read(self, size=-1):
        """Read at most size bytes from the file (less if the read hits EOF before obtaining size bytes). If the size
        argument is negative or omitted, read all data until EOF is reached. The bytes are returned as a string object.
        An empty string is returned when EOF is encountered immediately. (For certain files, like ttys, it makes sense
        to continue reading after an EOF is hit.) Note that this method may call the underlying C function fread() more
        than once in an effort to acquire as close to size bytes as possible. Also note that when in non-blocking mode,
        less data than what was requested may be returned, even if no size parameter was given.
        """
        return self.format_read(self.fp.read(size), self.mode)

    def readline(self, size=-1):
        """Read one entire line from the file. A trailing newline character is kept in the string (but may be absent
        when a file ends with an incomplete line).2.11 If the size argument is present and non-negative, it is a
        maximum byte count (including the trailing newline) and an incomplete line may be returned. An empty string
        is returned only when EOF is encountered immediately. Note: Unlike stdio's fgets(), the returned string
        contains null characters ('\0') if they occurred in the input.
        """
        try:
            return self.format_read(self.fp.readline(size), self.mode)
        except (AttributeError, Exception):
            if 'b' in self.mode:
                return b''
            else:
                return ''

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

    def __getattr__(self, item):
        return getattr(self.fp, item)
