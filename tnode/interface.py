import os
import contextlib
import pathlib
import json
from dynamicmethod import dynamicmethod
from collections import OrderedDict

from .file_utils import FileWrapper


__all__ = ['TNode', 'is_file_path', 'open_file']


def is_file_path(filename):
    return isinstance(filename, (str, bytes, pathlib.Path)) or hasattr(filename, '__fspath__')



open_file = FileWrapper


class TNode(object):
    DELIM = ' > '

    @dynamicmethod
    def get_delimiter(cls_self):
        return cls_self.DELIM

    @dynamicmethod
    def set_delimiter(cls_self, delim):
        cls_self.DELIM = delim

    def __init__(self, title='', *child, children=None, parent=None, data=None, **kwargs):
        self._title = title
        self._parent = None
        self._children = []

        # Set given keyword arguments as attributes
        for k, v in kwargs.items():
            setattr(self, k, v)

        # Add children
        if children is None:
            children = []
        children.extend(child)
        for child in children:
            self.add_child(child)

        # Add parent
        if parent is not None:
            self.parent = parent
        if data is not None:
            self.set_data(data)

    def validate_parent(self, parent):
        """Validate that this parent object is allowed to be a parent.

        Raises and error when this parent is not allowed to be set.
        """
        pass

    def get_parent(self):
        """Return the parent"""
        return self._parent

    def set_parent(self, parent):
        try:
            self._parent.remove_child(self)
        except (AttributeError, ValueError, TypeError):
            pass

        if parent is not None:
            self.validate_parent(parent)
        self._parent = parent
        try:
            self._parent.add_child(self)
        except (AttributeError, ValueError, TypeError):
            pass

    @property
    def parent(self):
        """Return the parent."""
        return self.get_parent()

    @parent.setter
    def parent(self, parent):
        """Set the parent. This property calls set_parent, so inheritance can just override set_parent()."""
        self.set_parent(parent)

    def get_parents(self, require_title=False):
        """Iterate through the parents"""
        p = self.parent
        while True:
            t = getattr(p, 'title', None)
            if p is None or (require_title and (not t or not isinstance(t, str))):
                break

            yield p
            p = getattr(p, 'parent', None)

    @property
    def title(self):
        """Return the title of this Node"""
        return self._title

    @title.setter
    def title(self, title):
        """Set the title of this Node"""
        if title is None:
            title = ''
        if self._parent and title in self._parent:
            raise ValueError('Title already exists in parent!')

        self._title = title

    @property
    def full_title(self):
        """Return the full title with the parent title's separated by the delimiter."""
        tt = [self.title] + [p.title for p in self.get_parents(require_title=True)]
        return self.get_delimiter().join(reversed(tt))

    key = full_title

    def depth(self):
        """Return the depth of this node."""
        return len(list(self.get_parents()))

    def validate_child(self, child):
        """Validate that this child object is allowed to be a child.

        Raises and error when this child is not allowed to be added.
        """
        pass

    def add_child(self, child):
        """Add the given child"""
        self.validate_child(child)

        try:
            if getattr(child, 'parent', None) != self:
                child.parent = self
        except AttributeError:
            pass

        if child not in self._children:
            self._children.append(child)

        return child

    def remove_child(self, child):
        """Remove the given child"""
        self._children.remove(child)

        try:
            if getattr(child, 'parent', None):
                child.parent = None
        except AttributeError:
            pass
        return child

    def clear(self):
        """Clear all children."""
        for i in reversed(range(len(self._children))):
            try:
                child = self._children.pop(i)
                child.parent = None
            except (AttributeError, Exception):
                pass

    def exists(self, child):
        """Return if the child exists."""
        return child in self

    def update(self, d=None, **kwargs):
        """Update the values of this node."""
        if d is None:
            d = kwargs
        elif not isinstance(d, dict):
            raise TypeError('Update requires a dictionary or keyword arguments.')
        else:
            d.update(kwargs)

        children = d.pop('children', None)
        if children:
            for child in children:
                self.add_child(child)

        for k, v in d.items():
            setattr(self, k, v)

    def find_parent(self, full_title, create_missing=False):
        """Find the full_title's parent and base title."""
        if not isinstance(full_title, str):
            try:
                full_title = full_title.full_title
            except (AttributeError, Exception) as err:
                raise TypeError('Invalid full_title given! This must be a str or TNode') from err

        split = full_title.split(self.get_delimiter())
        if split[0] == self.title:
            split = split[1:]

        parent = self
        for t in split[:-1]:
            for child in getattr(parent, 'children', []):
                if child.title == t:
                    parent = child
                    break
            else:
                if create_missing:
                    parent = parent.add_child(self.__class__(t))
                else:
                    raise KeyError('"{}" not found in {}'.format(t, parent))

        return parent, split[-1]

    def find(self, full_title):
        """Find and return the child that may be several levels deep."""
        parent, title = self.find_parent(full_title)

        for child in getattr(parent, 'children', []):
            if child.title == title:
                return child

        raise KeyError('"{}" not found in {}'.format(title, parent))

    def iter_children(self):
        """Iterate through my direct children only."""
        for child in self._children:
            yield child

    @property
    def children(self):
        """Return a list of child objects."""
        return list(self._children)

    def iter(self):
        """Iterate through each child and their children."""
        for child in self.iter_children():
            yield child
            if len(child) > 0:
                try:
                    yield from child.iter()
                except (AttributeError, TypeError):
                    pass

    def iter_nearest(self):
        """Iterate the nearest children first."""
        children = self.children
        while children:
            sub = []
            for child in children:
                yield child
                for ch in getattr(child, 'children', []):
                    sub.append(ch)
            children = sub

    def __iter__(self):
        return self.iter()

    def __len__(self):
        return len(self._children)

    def __bool__(self):
        return True  # This is not None. Do not return True or False based on empty children

    def __contains__(self, item):
        try:
            self.__getitem__(item)
            return True
        except (IndexError, KeyError, Exception) as err:
            return False

    def __getitem__(self, full_title):
        if isinstance(full_title, int):
            return self._children[full_title]
        elif isinstance(full_title, TNode):
            for child in self._children:
                if child == full_title:
                    return child

            # Get the full title
            full_title = full_title.full_title

        # Get the lowest level parent
        parent, title = self.find_parent(full_title)

        # Find if there is a child with the same title
        for ch in getattr(parent, 'children', []):
            if getattr(ch, 'title', None) == title:
                return ch

        raise KeyError('"{}" not found in {}'.format(title, parent))

    def __setitem__(self, full_title, child):
        parent = self
        if isinstance(full_title, int):
            index = full_title
            try:
                parent._children[index] = child
            except IndexError:
                parent._children.append(child)
            except AttributeError:
                pass

            try:
                parent.add_child(child)
            except (AttributeError, Exception):
                pass
            return

        # Get the lowest level parent
        parent, title = self.find_parent(full_title, create_missing=True)

        # Find if there is a child with the same title
        for i, ch in enumerate(getattr(parent, 'children', [])):
            if getattr(ch, 'title', None) == title:
                try:
                    if title != child.title:
                        child.title = title
                except (AttributeError, Exception):
                    pass
                try:
                    parent[i] = child  # This is a questionable way to set the child to the parent at the index.
                except (TypeError, Exception):
                    pass
                try:
                    parent.add_child(child)
                except (AttributeError, Exception):
                    pass
                return

        # Add the child
        try:
            if title != child.title:
                child.title = title
        except (AttributeError, Exception):
            pass
        try:
            parent.add_child(child)
        except (AttributeError, Exception):
            pass

    def __eq__(self, other):
        if isinstance(other, str):
            return other == self.title or other == self.full_title
        return super(TNode, self).__eq__(other)

    def __hash__(self):
        return hash(self.full_title)

    def __str__(self):
        d = {'cls': self.__class__.__name__, 'full_title': self.full_title, 'title': self.title}
        return '{cls}(full_title={full_title!r})'.format(**d)

    def __repr__(self):
        return '<{} at 0x{:016X}>'.format(self.__str__(), id(self))  # "<TNode(full_title=) at 0x0000000000000000>"

    def has_data(self):
        """Helper to return if this function has data."""
        return getattr(self, '_data', None) is not None

    def get_data(self):
        """Return the data stored."""
        return getattr(self, '_data', None)

    def set_data(self, data):
        """Set the stored data."""
        setattr(self, '_data', data)

    data = property(get_data, set_data)

    def to_dict(self, exclude=None, **kwargs):
        """Return this tree as a dictionary of data.

        Args:
            exclude (list): List of full_title's to exclude. This can also exclude a parent and everything below it.
        """
        if exclude is None:
            exclude = []

        tree = {}
        if self.full_title not in exclude:
            tree = {'title': self.title}
            if len(self) > 0:
                tree['children'] = []
            if self.has_data():
                tree['data'] = self.get_data()

            for child in self.iter_children():
                tree['children'].append(child.to_dict(exclude=exclude, **kwargs))

        return tree

    asdict = to_dict

    @classmethod
    def from_dict(cls, d, tree=None):
        """Create a tree from the given dictionary.

        Args:
            d (dict): Dictionary of tree items.
            tree (TNode)[None]: Parent tree node to add items to. If None create a top level parent.

        Returns:
            tree (TNode): Tree (TNode) object that was created.
        """
        children = d.pop('children', [])
        if tree is None:
            tree = cls()  # self is the class and this was called as a classmethod

        # Set all d items as attributes
        for attr, val in d.items():
            try:
                setattr(tree, attr, val)
            except (AttributeError, TypeError, Exception):
                pass

        for child_d in children:
            child = cls.from_dict(child_d)
            child.parent = tree

        return tree

    fromdict = from_dict

    SAVE_EXT = {}
    LOAD_EXT = {}

    is_file_path = staticmethod(is_file_path)
    open_file = staticmethod(open_file)

    @classmethod
    def register_saver(cls, ext, func=None):
        if not isinstance(ext, str):
            raise TypeError('Invalid filename extension given to register!')

        if func is None:
            def decorator(func):
                return cls.register_saver(ext, func)
            return decorator

        cls.SAVE_EXT[str(ext).lower()] = func
        return func

    @classmethod
    def register_loader(cls, ext, func=None):
        if not isinstance(ext, str):
            raise TypeError('Invalid filename extension given to register!')

        if func is None:
            def decorator(func):
                return cls.register_loader(ext, func)
            return decorator

        if hasattr(func, '__func__'):
            func = func.__func__
        cls.LOAD_EXT[str(ext).lower()] = func
        return func

    def save(self, filename, ext=None, **kwargs):
        """Save this tree to a file.

        Args:
            filename (str): Filename or opened file object to save this tree node to.
            ext (str)[None]: File extension (Example: '.ini', '.json', ...). Must give if filename is file object.
            **kwargs (object/dict): Save function keyword arguments.
        """
        if ext is None:
            if self.is_file_path(filename):
                ext = os.path.splitext(str(filename))[-1]
            else:
                raise TypeError('Missing "ext" argument when "filename" was not a path!')

        func = self.SAVE_EXT.get(ext.lower(), None)
        if callable(func):
            return func(self, filename, **kwargs)

        raise ValueError('Invalid filename extension given!')

    @dynamicmethod
    def load(self, filename, ext=None, **kwargs):
        """load a tree from a file.

        Args:
            filename (str/TextIoWrapper): Filename or opened file object to read and load the tree from.
            ext (str)[None]: File extension (Example: '.ini', '.json', ...). Must give if filename is file object.
            **kwargs (object/dict): load function keyword arguments.
        """
        cls = self
        if isinstance(self, TNode):
            cls = self.__class__

        if ext is None:
            if self.is_file_path(filename):
                ext = os.path.splitext(str(filename))[-1]
            else:
                raise TypeError('Missing "ext" argument when "filename" was not a path!')

        func = self.LOAD_EXT.get(ext.lower(), None)
        if callable(func):
            bound = func.__get__(self, cls)
            return bound(filename, **kwargs)

        raise ValueError('Invalid filename extension given!')

    def to_json(self, filename, **kwars):
        d = self.to_dict()

        with self.open_file(filename, 'w') as file:
            json.dump(d, file, indent=2)

        return filename

    @dynamicmethod
    def from_json(self, filename, **kwargs):
        with self.open_file(filename, 'r') as file:
            d = json.load(file)

        kwargs = {}
        if isinstance(self, TNode):
            kwargs['tree'] = self
        return self.from_dict(d, **kwargs)


TNode.register_saver('.json', TNode.to_json)
TNode.register_loader('.json', TNode.from_json)
