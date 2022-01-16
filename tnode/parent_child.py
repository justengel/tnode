import json
import configparser
from dynamicmethod import dynamicmethod
from collections import OrderedDict
from .interface import TNode


__all__ = ['ParentNode', 'ChildNode']


class ParentNode(TNode):
    PARENT_TYPES = []
    CHILD_TYPES = []
    SAVE_EXT = {}
    LOAD_EXT = {}

    @classmethod
    def register_parent_type(cls, parent_cls):
        cls.PARENT_TYPES.append(parent_cls)
        return parent_cls

    @classmethod
    def register_child_type(cls, child_cls):
        cls.CHILD_TYPES.append(child_cls)
        return child_cls

    def __init__(self, title='', *child, children=None, parent=None, **kwargs):
        super(ParentNode, self).__init__(title, *child, children=children, parent=parent, **kwargs)

    def validate_parent(self, parent):
        parent_types = [p for p in self.PARENT_TYPES]
        if len(parent_types) == 0:
            parent_types.append(type(self))
        if parent is not None and not any(isinstance(parent, ptype) for ptype in parent_types):
            raise TypeError('Invalid parent node type!')

    def validate_child(self, child):
        if not any(isinstance(child, chtype) for chtype in self.CHILD_TYPES):
            raise TypeError('Invalid child node type!')

    def add(self, full_title, obj=None, child_type=None, **kwargs):
        """Add a child node to this parent or sub parent.

        Args:
            full_title (str): Full title path to add this parent object to.
            obj (object)[None]: Child Type object to add.
            child_type (type/class): Child type that should be used to create the child object. CHILD_TYPES[0]
            **kwargs (object/dict): Key word attributes to set.
        """
        parent, title = self.find_parent(full_title)

        if obj is not None:
            if obj.title != title:
                obj.title = title
            parent.add_child(obj)
        else:
            if child_type is None:
                try:
                    child_type = parent.CHILD_TYPES[0]
                except IndexError:
                    raise TypeError('No child types set!')

            if 'title' not in kwargs:
                kwargs['title'] = title
            obj = child_type(**kwargs)
            parent.add_child(obj)
        return obj

    def add_parent(self, full_title, obj=None, parent_type=None, **kwargs):
        """Add a parent node to this parent or a sub parent.

        Args:
            full_title (str): Full title path to add this parent object to.
            obj (object)[None]: Parent Type object to add.
            parent_type (type/class): Parent type that should be used to create the parent object. PARENT_TYPES[0]
            **kwargs (object/dict): Key word attributes to set.
        """
        parent, title = self.find_parent(full_title)

        if obj is not None:
            # Add the obj
            if obj.title != title:
                obj.title = title
            parent.add_child(obj)
        else:
            if parent_type is None:
                try:
                    parent_type = parent.PARENT_TYPES[0]
                except IndexError:
                    parent_type = type(parent)

            if 'title' not in kwargs:
                kwargs['title'] = title
            obj = parent_type(**kwargs)
            parent.add_child(obj)
        return obj

    def has_data(self):
        """Helper to return if this function has data."""
        return False

    def get_data(self):
        """Return the data stored."""
        return None

    def to_dict(self):
        """Return this tree as a dictionary of data."""
        tree = OrderedDict()

        # Check if top level has children nodes
        top = OrderedDict()
        for child in self.iter_children():
            if isinstance(child, tuple(self.CHILD_TYPES)) and child.has_data():
                top[child.full_title] = child.get_data()
        if len(top) > 0:
            tree[self.full_title] = top

        # Add all parent nodes to the top level with the full_title
        for child in self.iter():
            if child.full_title in top:
                continue  # Ignore already set items
            elif isinstance(child, tuple(self.PARENT_TYPES)):
                tree[child.full_title] = OrderedDict()
            elif isinstance(child, tuple(self.CHILD_TYPES)) and child.has_data():
                tree[child.parent.full_title][child.title] = child.get_data()

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
        if tree is None:
            tree = cls()  # self is the class and this was called as a classmethod

        # Set the default items as direct children of the top level node
        if '' in d or 'DEFAULT' in d:
            children = d.pop('', d.pop('DEFAULT', {}))
            for title, data in children.items():
                tree.add(title, data=data)

        # Add sections and their children
        for full_title, children in d.items():
            p = tree.add_parent(full_title)
            for title, data in children.items():
                p.add(title, data=data)

        return tree

    fromdict = from_dict

    def to_ini(self, filename, **kwargs):
        cfg = configparser.ConfigParser()
        cfg.optionxform = str  # Make option names case-sensitive

        # Get dict and convert to valid string values
        d = self.to_dict()
        for k, v in d.items():
            if isinstance(v, dict):
                # Convert section
                for k2, v2 in v.items():
                    v[k2] = json.dumps(v2)
            else:
                d[k] = json.dumps(v)

        if '' in d:
            d['DEFAULT'] = d.pop('')
        cfg.read_dict(d)

        with open(filename, 'w') as f:
            cfg.write(f)

        return filename

    @dynamicmethod
    def from_ini(cls, filename, **kwargs):
        cfg = configparser.ConfigParser()
        cfg.optionxform = str  # Make option names case-sensitive
        cfg.read(filename)

        # Create a dictionary to load from
        d = OrderedDict()
        # Note cfg._sections works while cfg.items() does not!
        for full_title, section in [('DEFAULT', cfg.defaults())] + list(cfg._sections.items()):
            sect = OrderedDict()
            if full_title == '' or full_title == 'DEFAULT':
                d[''] = sect
            else:
                d[full_title] = sect

            # Add child items
            for title, value in section.items():
                sect[title] = json.loads(value)

        # Load using from_dict. Yes, this is slower (iter 2x), but keeps consistency
        kwds = {}
        if isinstance(cls, TNode):
            kwds['tree'] = cls
        return cls.from_dict(d, **kwds)


# Register save/load for this class
ParentNode.register_saver('.json', ParentNode.to_json)
ParentNode.register_loader('.json', ParentNode.from_json)
ParentNode.register_saver('.ini', ParentNode.to_ini)
ParentNode.register_loader('.ini', ParentNode.from_ini)
ParentNode.register_saver('.conf', ParentNode.to_ini)
ParentNode.register_loader('.conf', ParentNode.from_ini)


class ChildNode(TNode):
    PARENT_TYPES = []
    CHILD_TYPES = []
    SAVE_EXT = {}
    LOAD_EXT = {}

    @classmethod
    def register_parent_type(cls, parent_cls):
        cls.PARENT_TYPES.append(parent_cls)
        return parent_cls

    @classmethod
    def register_child_type(cls, child_cls):
        cls.CHILD_TYPES.append(child_cls)
        return child_cls

    def __init__(self, title='', parent=None, data=None, **kwargs):
        super(ChildNode, self).__init__(title, parent=parent, data=data, **kwargs)

    def validate_parent(self, parent):
        if parent is not None and not any(isinstance(parent, ptype) for ptype in self.PARENT_TYPES):
            raise TypeError('Invalid parent node type!')

    def validate_child(self, child):
        raise TypeError('Child nodes cannot have more children!')

    to_json = ParentNode.to_json
    from_json = ParentNode.from_json
    to_ini = ParentNode.to_ini
    from_ini = ParentNode.from_ini


# Register save/load for this class
ChildNode.register_saver('.json', ChildNode.to_json)
ChildNode.register_loader('.json', ChildNode.from_json)
ChildNode.register_saver('.ini', ChildNode.to_ini)
ChildNode.register_loader('.ini', ChildNode.from_ini)
ChildNode.register_saver('.conf', ChildNode.to_ini)
ChildNode.register_loader('.conf', ChildNode.from_ini)
