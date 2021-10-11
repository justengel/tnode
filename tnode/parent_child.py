from .interface import TNode


__all__ = ['ParentNode', 'ChildNode']


class ParentNode(TNode):
    PARENT_TYPES = []
    CHILD_TYPES = []

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

    def add(self, full_title, obj=None, **kwargs):
        """Add a child node to this parent or sub parent.

        Args:
            full_title (str): Full title path to add this parent object to.
            obj (object)[None]: Child Type object to add.
            **kwargs (object/dict): Key word attributes to set.
        """
        parent, title = self.find_parent(full_title)

        if obj is not None:
            if obj.title != title:
                obj.title = title
            parent.add_child(obj)
        else:
            try:
                ch_type = self.CHILD_TYPES[0]
            except IndexError:
                raise TypeError('No child types set!')

            if 'parent' not in kwargs:
                kwargs['parent'] = parent
            if 'title' not in kwargs:
                kwargs['title'] = title
            obj = ch_type(**kwargs)
        return obj

    def add_parent(self, full_title, obj=None, **kwargs):
        """Add a parent node to this parent or a sub parent.

        Args:
            full_title (str): Full title path to add this parent object to.
            obj (object)[None]: Parent Type object to add.
            **kwargs (object/dict): Key word attributes to set.
        """
        parent, title = self.find_parent(full_title)

        if obj is not None:
            # Add the obj
            if obj.title != title:
                obj.title = title
            parent.add_child(obj)
        else:
            try:
                p_type = self.CHILD_TYPES[0]
            except IndexError:
                p_type = type(parent)

            if 'parent' not in kwargs:
                kwargs['parent'] = parent
            if 'title' not in kwargs:
                kwargs['title'] = title

            obj = p_type(**kwargs)
        return obj

    def has_data(self):
        """Helper to return if this function has data."""
        return False

    def get_data(self):
        """Return the data stored."""
        return None


class ChildNode(TNode):
    PARENT_TYPES = []
    CHILD_TYPES = []

    @classmethod
    def register_parent_type(cls, parent_cls):
        cls.PARENT_TYPES.append(parent_cls)
        return parent_cls

    @classmethod
    def register_child_type(cls, child_cls):
        cls.CHILD_TYPES.append(child_cls)
        return child_cls

    def __init__(self, title='', parent=None, **kwargs):
        super(ChildNode, self).__init__(title, parent=parent, **kwargs)

    def validate_parent(self, parent):
        if parent is not None and not any(isinstance(parent, ptype) for ptype in self.PARENT_TYPES):
            raise TypeError('Invalid parent node type!')

    def validate_child(self, child):
        raise TypeError('Child nodes cannot have more children!')

    def has_data(self):
        """Helper to return if this function has data."""
        return False

    def get_data(self):
        """Return the data stored."""
        return None
