import configparser
from dynamicmethod import dynamicmethod
from collections import OrderedDict
from .interface import TNode

try:
    from dataclasses import MISSING
except (ImportError, Exception):
    class MISSING(object):
        pass


__all__ = ['ParentNode', 'ChildNode']


class ParentChildRegistration:
    PARENT_TYPES = []
    CHILD_TYPES = []

    @classmethod
    def register_parent_type(cls, parent_cls):
        cls.PARENT_TYPES.append(parent_cls)
        return parent_cls

    @classmethod
    def remove_parent_type(cls, parent_cls):
        try:
            cls.PARENT_TYPES.remove(parent_cls)
        except(TypeError, ValueError, Exception):
            pass

    @classmethod
    def clear_parent_types(cls):
        cls.CHILD_TYPES.clear()

    @classmethod
    def register_child_type(cls, child_cls):
        cls.CHILD_TYPES.append(child_cls)
        return child_cls

    @classmethod
    def remove_child_type(cls, child_cls):
        try:
            cls.CHILD_TYPES.remove(child_cls)
        except(TypeError, ValueError, Exception):
            pass

    @classmethod
    def clear_child_types(cls):
        cls.CHILD_TYPES.clear()


class ParentNode(TNode, ParentChildRegistration):
    PARENT_TYPES = []
    CHILD_TYPES = []
    SAVE_EXT = {}
    LOAD_EXT = {}

    def __init__(self, title='', *child, children=None, parent=None, **kwargs):
        super(ParentNode, self).__init__(title, *child, children=children, parent=parent, **kwargs)

    def validate_parent(self, parent):
        parent_types = [p for p in self.PARENT_TYPES]
        if len(parent_types) == 0:
            parent_types.append(type(self))
        if parent is not None and not any(isinstance(parent, ptype) for ptype in parent_types):
            raise TypeError('Invalid parent node type "{}"!'.format(type(parent).__name__))

    def validate_child(self, child):
        if not any(isinstance(child, chtype) for chtype in self.CHILD_TYPES):
            raise TypeError('Invalid child node type "{}"!'.format(type(child).__name__))

    def add(self, full_title, obj=None, *_, child_type=None, create_missing=False, **kwargs):
        """Add a child node to this parent or sub parent.

        Args:
            full_title (str): Full title path to add this parent object to.
            obj (object)[None]: Child Type object to add.
            child_type (type/class): Child type that should be used to create the child object. CHILD_TYPES[0]
            create_missing (bool)[False]: If True create the missing parents else raise an error if a parent is missing.
            **kwargs (object/dict): Key word attributes to set.
        """
        parent, title = self.find_parent(full_title, create_missing=create_missing)

        if obj is not None:
            if obj.title != title:
                obj.title = title
            if obj not in parent:
                parent.add_child(obj)
        else:
            if child_type is None:
                try:
                    child_type = parent.CHILD_TYPES[0]
                except IndexError:
                    raise TypeError('No child types set!')

            # Get or create the child
            try:
                obj = parent[title]
            except KeyError:
                obj = child_type(title=title)
                parent.add_child(obj)

        obj.update(**kwargs)
        return obj

    def add_parent(self, full_title, obj=None, *_, parent_type=None, create_missing=False, **kwargs):
        """Add a parent node to this parent or a sub parent.

        Args:
            full_title (str): Full title path to add this parent object to.
            obj (object)[None]: Parent Type object to add.
            parent_type (type/class): Parent type that should be used to create the parent object. PARENT_TYPES[0]
            create_missing (bool)[False]: If True create the missing parents else raise an error if a parent is missing.
            **kwargs (object/dict): Key word attributes to set.
        """
        parent, title = self.find_parent(full_title, create_missing=create_missing)

        if obj is not None:
            # Add the obj
            if obj.title != title:
                obj.title = title
            if obj not in parent:
                parent.add_child(obj)
        else:
            if parent_type is None:
                try:
                    parent_type = parent.PARENT_TYPES[0]
                except IndexError:
                    parent_type = type(parent)

            # Get or create the child
            try:
                obj = parent[title]
            except KeyError:
                obj = parent_type(title=title)
                parent.add_child(obj)

        obj.update(kwargs)
        return obj

    def has_data(self):
        """Helper to return if this function has data."""
        return False

    def get_data(self):
        """Return the data stored."""
        return None

    def set_data(self, data):
        raise AttributeError("Parent objects cannot have data!")

    data = property(get_data, set_data)

    @classmethod
    def from_dict(cls, d, tree=None, **kwargs):
        """Create a tree from the given dictionary.

        Args:
            d (dict): Dictionary of tree items.
                Example: {'title': title, 'data': data, 'children': [{'title': title, 'data': data}]}
            tree (TNode)[None]: Parent tree node to add items to. If None create a top level parent.

        Returns:
            tree (TNode): Tree (TNode) object that was created.
        """
        children = d.pop('children', [])
        title = d.pop('title', '')
        if tree is None:
            tree = cls(title=title)
        elif not tree.title and title:
            tree.title = title

        # Set all d items as attributes
        for attr, val in d.items():
            try:
                setattr(tree, attr, val)
            except (AttributeError, TypeError, Exception):
                pass

        for child_d in children:
            if 'data' not in child_d:
                p = tree.add_parent(child_d.pop('title', ''), create_missing=True)
                p.from_dict(child_d, tree=p, **kwargs)
            else:
                c = tree.add(child_d.pop('title', ''), create_missing=True)
                c.from_dict(child_d, tree=c, **kwargs)

        return tree

    fromdict = from_dict

    def to_ini_dict(self, d, parent_key='', delimiter=None, tree=None, include_empty_parents=True, **kwargs):
        """Convert a nested dictionary of {'title': title, 'data': data, 'children': [{'title': title, 'data': data}]}
        to an simple init dict {'section': {'title': value, 'title2': value}, 'sub section': {'title': value}}

        Args:
            d (OrderedDict/dict): Dictionary {'title': title, 'children': [{'title': title, 'data': data}]}
            parent_key (str)['']: This dictionary's parent key.
            delimiter (str)[None]: Parent key separator
            tree (dict)[None]: Dictionary to stuff items into.
            include_empty_parents (bool)[True]: If True add parents that have no data or children.

        Returns:
            tree (OrderedDict): Ini dict {'section': {'title': value, 'title2': value}, 'sub section': {'title': value}}
        """
        if tree is None:
            tree = OrderedDict()
        if delimiter is None:
            delimiter = self.get_delimiter()

        key = title = d.pop('title', '')
        if parent_key:
            key = parent_key + delimiter + title

        children = d.pop('children', [])
        data = d.pop('data', MISSING)

        if data is not MISSING:
            try:
                tree[parent_key][title] = data
            except (KeyError, Exception):
                tree[parent_key] = OrderedDict([(title, data)])
        elif children:
            for child in children:
                self.to_ini_dict(child, key, delimiter, tree, include_empty_parents=include_empty_parents, **kwargs)
        elif include_empty_parents:
            tree[key] = OrderedDict()

        return tree

    @classmethod
    def from_ini_dict(cls, d):
        """Convert an ini dict to the standard dict format."""
        tree = OrderedDict([('title', ''), ('children', [])])

        # If default ('') add children to top level
        if '' in d:
            section = d.pop('')
            for title, value in section.items():
                tree['children'].append(OrderedDict([('title', title), ('data', value)]))

        # Add subsections
        for name, section in d.items():
            sect = OrderedDict([('title', name), ('children', [])])
            tree['children'].append(sect)

            for title, value in section.items():
                sect['children'].append(OrderedDict([('title', title), ('data', value)]))

        return tree

    def to_ini(self, filename, include_empty_parents=True, **kwargs):
        cfg = configparser.ConfigParser(allow_no_value=True, strict=False, inline_comment_prefixes=(";"))
        cfg.optionxform = str  # Make option names case-sensitive

        # Get dict and convert to valid string values
        d = self.to_dict()

        # Flatten dict
        d = self.to_ini_dict(d, '', self.get_delimiter(), include_empty_parents=include_empty_parents)
        for g_name, group in d.items():
            for k, v in group.items():
                group[k] = self.serialize(v)

        if '' in d:
            d['DEFAULT'] = d.pop('')
        cfg.read_dict(d)

        with self.open_file(filename, 'w') as f:
            cfg.write(f)

        return filename

    @dynamicmethod
    def from_ini(cls, filename, **kwargs):
        cfg = configparser.ConfigParser(allow_no_value=True, strict=False, inline_comment_prefixes=(";"))
        cfg.optionxform = str  # Make option names case-sensitive

        # cfg.read(filename)
        with cls.open_file(filename, 'r') as file:
            cfg.read_file(file)

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
                sect[title] = cls.deserialize(value)

        # Load using from_dict. Yes, this is slower (iter 2x), but keeps consistency
        kwds = {}
        if isinstance(cls, TNode):
            kwds['tree'] = cls
        return cls.from_dict(cls.from_ini_dict(d), **kwds)


# Register save/load for this class
ParentNode.register_saver('.json', ParentNode.to_json)
ParentNode.register_loader('.json', ParentNode.from_json)
ParentNode.register_saver('.ini', ParentNode.to_ini)
ParentNode.register_loader('.ini', ParentNode.from_ini)
ParentNode.register_saver('.conf', ParentNode.to_ini)
ParentNode.register_loader('.conf', ParentNode.from_ini)


class ChildNode(TNode, ParentChildRegistration):
    PARENT_TYPES = []
    CHILD_TYPES = []
    SAVE_EXT = {}
    LOAD_EXT = {}

    def __init__(self, title='', parent=None, data=None, **kwargs):
        super(ChildNode, self).__init__(title, parent=parent, data=data, **kwargs)

    def validate_parent(self, parent):
        if parent is not None and not any(isinstance(parent, ptype) for ptype in self.PARENT_TYPES):
            raise TypeError('Invalid parent node type "{}"!'.format(type(parent).__name__))

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
