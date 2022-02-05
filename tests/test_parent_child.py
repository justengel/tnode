import os
from tnode import ParentNode, ChildNode


class Parent(ParentNode):
    pass


class Child(ChildNode):
    def __init__(self, title='', data=None, parent=None, **kwargs):
        super().__init__(title=title, data=data, parent=parent, **kwargs)

    def has_data(self):
        """Helper to return if this function has data."""
        return True

    def get_data(self):
        """Return the data stored."""
        return self._data

    def set_data(self, data):
        """Set the data stored."""
        self._data = data

    data = property(get_data, set_data)


Child.register_parent_type(Parent)
Parent.register_child_type(Child)  # Register the child type first!
Parent.register_parent_type(Parent)
Parent.register_child_type(Parent)


def test_add():
    top = Parent('')
    parent1 = top.add_parent('parent1')
    parent2 = top.add_parent('parent2')
    subparent1 = top.add_parent('parent1 > subparent1')

    child1 = top.add('child1', data=1)
    child2 = top.add('parent1 > child2', data=2)
    child3 = top.add('parent1 > subparent1 > child3', data=3)


def test_json(remove_file=True):
    top = Parent('')
    parent1 = top.add_parent('parent1')
    parent2 = top.add_parent('parent2')
    subparent1 = top.add_parent('parent1 > subparent1')

    child1 = top.add('child1', data=1)
    child2 = top.add('parent1 > child2', data=2)
    child3 = top.add('parent1 > subparent1 > child3', data=3)
    child4 = top.add('parent1 > subparent1 > child4', data={'abc': 123})

    filename = 'test_json_parent_child.json'
    try:
        fname = top.to_json(filename)
        assert fname == filename
        t2 = Parent.from_json(fname)

        assert t2.to_dict() == top.to_dict()
        for child in top.iter():
            assert child.full_title in t2
            assert child.get_data() == t2[child.full_title].get_data()
    finally:
        try:
            if remove_file:
                os.remove(filename)
        except (OSError, Exception):
            pass

    # check that save/load works the same
    try:
        fname = top.save(filename)
        assert fname == filename
        t2 = Parent.load(fname)

        assert t2.to_dict() == top.to_dict()
        for child in top.iter():
            assert child.full_title in t2
            assert child.get_data() == t2[child.full_title].get_data()
    finally:
        try:
            if remove_file:
                os.remove(filename)
        except (OSError, Exception):
            pass

    # Load into node
    try:
        fname = top.save(filename)
        assert fname == filename

        new_node = Parent(title='new node')
        new_node.load(filename)  # Title stays the same!
        assert new_node.title == 'new node'
        assert len(new_node) > 0

        # Change title to make things easier to compare
        new_node.title = ''
        assert new_node.to_dict() == top.to_dict()
        for child in top.iter():
            assert child.full_title in new_node
            assert child.get_data() == new_node[child.full_title].get_data()
    finally:
        try:
            if remove_file:
                os.remove(filename)
        except (OSError, Exception):
            pass


def test_ini(remove_file=True):
    top = Parent('')
    parent1 = top.add_parent('parent1')
    parent2 = top.add_parent('parent2')
    subparent1 = top.add_parent('parent1 > subparent1')

    child1 = top.add('child1', data=1)
    child2 = top.add('parent1 > child2', data=2)
    child3 = top.add('parent1 > subparent1 > child3', data=3)
    child4 = top.add('parent1 > subparent1 > child4', data={'abc': 123})

    filename = 'test_json_parent_child.ini'
    try:
        t2 = top.from_ini(top.to_ini(filename))

        assert t2.to_dict() == top.to_dict()
        for child in top.iter():
            assert child.full_title in t2
            assert child.get_data() == t2[child.full_title].get_data()
    finally:
        try:
            if remove_file:
                os.remove(filename)
        except (OSError, Exception):
            pass

    # check that save/load works the same
    try:
        fname = top.save(filename)
        assert fname == filename
        t2 = Parent.load(fname)

        assert t2.to_dict() == top.to_dict()
        for child in top.iter():
            assert child.full_title in t2
            assert child.get_data() == t2[child.full_title].get_data()
    finally:
        try:
            if remove_file:
                os.remove(filename)
        except (OSError, Exception):
            pass

    # Load into node
    try:
        fname = top.save(filename)
        assert fname == filename

        new_node = Parent(title='new node')
        new_node.load(filename)  # Overrides attribute title! {title: ''}
        assert new_node.title == 'new node'
        assert len(new_node) > 0

        # Change title to make things easier to compare
        new_node.title = ''
        assert new_node.to_dict() == top.to_dict()
        for child in top.iter():
            assert child.full_title in new_node
            assert child.get_data() == new_node[child.full_title].get_data()
    finally:
        try:
            if remove_file:
                os.remove(filename)
        except (OSError, Exception):
            pass


if __name__ == '__main__':
    test_add()
    test_json()
    test_ini()
