import os
import json
from collections import OrderedDict


__all__ = ['TNode']


class TNode(object):
    DELIM = ' > '

    @classmethod
    def get_delimiter(cls):
        return cls.DELIM

    @classmethod
    def set_delimiter(cls, delim):
        cls.DELIM = delim

    def __init__(self, title='', *child, children=None, parent=None, **kwargs):
        super().__init__()

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

    def remove_child(self, child):
        """Remove the given child"""
        self._children.remove(child)

        try:
            if getattr(child, 'parent', None):
                child.parent = None
        except AttributeError:
            pass

    def clear(self):
        """Clear all children."""
        for i in reversed(range(len(self._children))):
            try:
                child = self._children.pop(i)
                child.parent = None
            except (AttributeError, Exception):
                pass

    def find_parent(self, full_title):
        """Find the full_title's parent and base title."""
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
        return len(list(self.iter()))

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
        parent, title = self.find_parent(full_title)

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

    def __str__(self):
        d = {'cls': self.__class__.__name__, 'full_title': self.full_title, 'title': self.title}
        return '{cls}(full_title={full_title!r})'.format(**d)

    def __repr__(self):
        return '<{} at 0x{:016X}>'.format(self.__str__(), id(self))  # "<TNode(full_title=) at 0x0000000000000000>"

    def has_data(self):
        """Helper to return if this function has data."""
        return False

    def get_data(self):
        """Return the data stored."""
        return None

    def asdict(self):
        """Return this tree as a dictionary of data."""
        tree = {'title': self.title}

        if len(self) > 0:
            tree['children'] = []
        if self.has_data():
            tree['data'] = self.get_data()

        for child in self.iter_children():
            tree['children'].append(child.asdict())

        return tree

    @classmethod
    def fromdict(cls, d):
        children = d.pop('children', [])
        node = cls(**d)

        for child_d in children:
            child = cls.fromdict(child_d)
            child.parent = node

        return node

    SAVE_EXT = {}
    LOAD_EXT = {}

    @classmethod
    def register_saver(cls, ext, func=None):
        if func is None:
            def decorator(func):
                return cls.register_saver(ext, func)
            return decorator

        cls.SAVE_EXT[str(ext).lower()] = func
        return func

    @classmethod
    def register_loader(cls, ext, func=None):
        if func is None:
            def decorator(func):
                return cls.register_loader(ext, func)
            return decorator

        cls.LOAD_EXT[str(ext).lower()] = func
        return func

    def save(self, filename, **kwargs):
        """Save this tree to a file.

        Args:
            filename (str): Filename to save this tree node to.
            **kwargs (object/dict): Save function keyword arguments.
        """
        ext = os.path.splitext(filename)[-1]
        func = self.SAVE_EXT.get(ext.lower(), None)
        if callable(func):
            return func(tree, filename, **kwargs)

        raise ValueError('Invalid filename extension given!')

    @classmethod
    def load(cls, filename, **kwargs):
        """load a tree from a file.

        Args:
            filename (str): Filename to read and load the tree from.
            **kwargs (object/dict): load function keyword arguments.
        """
        ext = os.path.splitext(filename)[-1]
        func = cls.LOAD_EXT.get(ext.lower(), None)
        if callable(func):
            return func(filename, **kwargs)

        raise ValueError('Invalid filename extension given!')

    def to_json(self, filename, **kwars):
        d = self.asdict()
        with open(filename, 'w') as file:
            json.dump(d, file)
        return filename

    @classmethod
    def from_json(cls, filename, **kwargs):
        with open(filename, 'r') as file:
            d = json.load(file)
        return cls.fromdict(d)


TNode.register_saver('.json', TNode.to_json)
TNode.register_loader('.json', TNode.from_json)
