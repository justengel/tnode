import os
from tnode import ParentNode, ChildNode


class Parent(ParentNode):
    pass


class Child(ChildNode):
    def __init__(self, title='', data=None, parent=None, **kwargs):
        self.data = data
        super().__init__(title=title, parent=parent, **kwargs)

    def has_data(self):
        """Helper to return if this function has data."""
        return True

    def get_data(self):
        """Return the data stored."""
        return self.data


Parent.register_parent_type(Parent)
Parent.register_child_type(Parent)
Parent.register_child_type(Child)
Child.register_parent_type(Parent)


def test_add():
    top = Parent('')
    parent1 = top.add_parent('parent1')
    parent2 = top.add_parent('parent2')
    subparent1 = top.add_parent('parent1 > subparent1')

    child1 = top.add('child1', data=1)
    child2 = top.add('parent1 > child2', data=2)
    child3 = top.add('parent1 > subparent1 > child3', data=3)


def test_json():
    top = Parent('')
    parent1 = top.add_parent('parent1')
    parent2 = top.add_parent('parent2')
    subparent1 = top.add_parent('parent1 > subparent1')

    child1 = top.add('child1', data=1)
    child2 = top.add('parent1 > child2', data=2)
    child3 = top.add('parent1 > subparent1 > child3', data=3)

    filename = 'test_json_parent_child.json'
    try:
        t2 = top.from_json(top.to_json(filename))

        for v1, v2 in zip(top.iter(), t2.iter()):
            assert v1.full_title == v2.full_title
            assert v1.get_data() == v2.get_data()
    finally:
        try:
            os.remove(filename)
        except (OSError, Exception):
            pass


if __name__ == '__main__':
    test_add()
    test_json()
