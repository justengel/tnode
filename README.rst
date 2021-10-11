=====
TNode
=====

Tree node

Classes:
  * TNode - Single node approach that can have any number of children
  * Parent - Parent/Child nodes. Parent can have children of specific types.
  * Child - Parent/Child nodes. Child cannot have children, but can have a parent of specific types.

Attributes
  * parent - parent object or None
  * title - String title for this node (Can be '')
  * children - List of child objects
  * full_title - Parent titles and this title separeted by the set delimiter

Methods
  * get_parents(require_title=False) - Iterate through the parent objects
  * add_child(child) - Add a child object
  * remove_child(child) - Remove a child object
  * clear() - Clear all direct children
  * find_parent(full_title) - Return the parent and title from the given full title.
  * find(full_title) - Return the child object with the given full title.
  * iter_children() - Iterate through the direct children.
  * __iter__() - Iterate through the direct children.
  * iter() - Iterate though all children and children's children.
  * iter_nearest() - Iterate through direct children then their children's children.
  * __getitem__(full_title) - Return the child object with the given full title.
  * __setitem__(full_title, child) - Add the child to the proper parent with the full title.
  * __len__() - Return the length of the direct children.


Example
=======

Create the tree nodes.

.. code-block:: python

    from tnode import TNode

    t = TNode()
    parent1 = TNode('parent1', parent=t)
    child1 = TNode('child1', parent=parent1)
    child2 = TNode('child2', parent=parent1)
    parent2 = TNode('parent2', parent=parent1)
    child3 = TNode('child3', parent=parent2)
    child4 = TNode('child4', parent=parent2)

    assert list(t.iter()) == \
       [t,
        parent1,
            child1,
            child2,
            parent2,
                child3,
                child4]


Parent Child Example
====================

Create custom Parent and Child classes.

.. code-block:: python

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

    # Create tree
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
