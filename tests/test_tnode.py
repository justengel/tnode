import os


def test_init_and_properties():
    from tnode import TNode

    t = TNode()
    assert t.title == ''
    assert t.full_title == ''
    assert t.parent is None
    assert list(t) == []

    t = TNode(title='hello', parent='abc')
    assert t.title == 'hello'
    assert t.full_title == 'hello'
    assert t.parent == 'abc'
    assert list(t) == []

    t = TNode('title', 'child1', 'child2', parent='parent')
    assert t.title == 'title'
    assert t.full_title == 'title'
    assert t.parent == 'parent'
    assert list(t) == ['child1', 'child2']

    # Test initialization with parent and child
    t = TNode()
    parent1 = TNode('parent1', parent=t)
    assert parent1 in t

    child1 = TNode('child1', parent=parent1)
    child2 = TNode('child2', parent=parent1)
    assert child1 in parent1
    assert child2 in parent1
    assert child1 in t
    assert child2 in t

    child3 = TNode('child3')
    child4 = TNode('child4')
    parent2 = TNode('parent2', child3, child4)
    parent2.parent = t
    assert parent2 in t
    assert child3 in parent2
    assert child4 in parent2
    assert child3 in t
    assert child4 in t

    # Full Title
    assert t.full_title == ''
    assert parent1.full_title == 'parent1'
    assert child1.full_title == 'parent1 > child1'
    assert child2.full_title == 'parent1 > child2'
    assert parent2.full_title == 'parent2'
    assert child3.full_title == 'parent2 > child3'
    assert child4.full_title == 'parent2 > child4'


def test_get_parents():
    from tnode import TNode

    t = TNode()
    parent1 = TNode('parent1', parent=t)
    child1 = TNode('child1', parent=parent1)
    child2 = TNode('child2', parent=parent1)
    parent2 = TNode('parent2', parent=parent1)
    child3 = TNode('child3', parent=parent2)
    child4 = TNode('child4', parent=parent2)

    assert list(child2.get_parents()) == [parent1, t]
    assert list(child4.get_parents()) == [parent2, parent1, t]
    assert list(child2.get_parents(require_title=True)) == [parent1]
    assert list(child4.get_parents(require_title=True)) == [parent2, parent1]


def test_add_child():
    from tnode import TNode

    t = TNode()
    parent1 = TNode('parent1')
    t.add_child(parent1)
    assert parent1 in t

    child1 = TNode('child1')
    parent1.add_child(child1)
    assert child1 in parent1


def test_remove_child():
    from tnode import TNode

    t = TNode()
    parent1 = TNode('parent1', parent=t)
    t.remove_child(parent1)
    assert parent1 not in t

    child1 = TNode('child1', parent=parent1)
    parent1.remove_child(child1)
    assert child1 not in parent1


def test_clear():
    from tnode import TNode

    t = TNode()
    parent1 = TNode('parent1', parent=t)
    parent2 = TNode('parent2', parent=t)
    subparent2 = TNode('subparent2', parent=parent2)
    child6 = TNode('child6', parent=subparent2)
    child7 = TNode('child7', parent=subparent2)

    child1 = TNode('child1', parent=parent2)
    child2 = TNode('child2', parent=parent1)
    child3 = TNode('child3', parent=parent1)
    subparent1 = TNode('subparent1', parent=parent1)
    child4 = TNode('child4', parent=subparent1)
    child5 = TNode('child5', parent=subparent1)

    assert len(subparent1) > 0
    subparent1.clear()
    assert len(subparent1) == 0
    assert child4.parent is None
    assert child5.parent is None

    assert len(parent2) > 0
    parent2.clear()
    assert len(parent2) == 0
    assert subparent2.parent is None
    assert child1.parent is None

    assert len(t) > 0
    t.clear()
    assert len(t) == 0
    assert parent1.parent is None
    assert parent2.parent is None


def test_find_parent():
    from tnode import TNode

    t = TNode()
    parent1 = TNode('parent1', parent=t)
    child1 = TNode('child1', parent=parent1)
    child2 = TNode('child2', parent=parent1)
    parent2 = TNode('parent2', parent=parent1)
    child3 = TNode('child3', parent=parent2)
    child4 = TNode('child4', parent=parent2)

    parent, title = t.find_parent('parent1')
    assert parent == t
    assert title == 'parent1'

    parent, title = t.find_parent('parent1 > child1')
    assert parent == parent1
    assert title == 'child1'

    parent, title = t.find_parent('parent1 > parent2')
    assert parent == parent1
    assert title == 'parent2'

    parent, title = t.find_parent('parent1 > parent2 > child3')
    assert parent == parent2
    assert title == 'child3'


def test_find():
    from tnode import TNode

    t = TNode()
    parent1 = TNode('parent1', parent=t)
    child1 = TNode('child1', parent=parent1)
    child2 = TNode('child2', parent=parent1)
    parent2 = TNode('parent2', parent=parent1)
    child3 = TNode('child3', parent=parent2)
    child4 = TNode('child4', parent=parent2)

    node = t.find('parent1')
    assert node == parent1

    node = t.find('parent1 > child1')
    assert node == child1

    node = t.find('parent1 > parent2')
    assert node == parent2

    node = t.find('parent1 > parent2 > child3')
    assert node == child3


def test_iter():
    from tnode import TNode

    t = TNode()
    parent1 = TNode('parent1', parent=t)
    parent2 = TNode('parent2', parent=t)
    subparent2 = TNode('subparent2', parent=parent2)
    child6 = TNode('child6', parent=subparent2)
    child7 = TNode('child7', parent=subparent2)

    child1 = TNode('child1', parent=parent2)
    child2 = TNode('child2', parent=parent1)
    child3 = TNode('child3', parent=parent1)
    subparent1 = TNode('subparent1', parent=parent1)
    child4 = TNode('child4', parent=subparent1)
    child5 = TNode('child5', parent=subparent1)

    # Test iter direct children
    assert list(t.iter_children()) == [parent1, parent2]
    assert list(parent1.iter_children()) == [child2, child3, subparent1]
    assert list(subparent1.iter_children()) == [child4, child5]
    assert list(parent2.iter_children()) == [subparent2, child1]
    assert list(subparent2.iter_children()) == [child6, child7]

    # Test iter all
    assert list(t.iter()) == \
           [parent1,
                child2,
                child3,
                subparent1,
                    child4,
                    child5,
            parent2,
                subparent2,
                    child6,
                    child7,
                child1]

    # Test iter all nearest
    assert list(t.iter_nearest()) == \
           [parent1,
            parent2,
                child2,
                child3,
                subparent1,
                subparent2,
                child1,
                    child4,
                    child5,
                    child6,
                    child7]

    # Test __iter__
    assert list(t) == \
           [parent1,
                child2,
                child3,
                subparent1,
                    child4,
                    child5,
            parent2,
                subparent2,
                    child6,
                    child7,
                child1]
    assert list(parent1) == \
           [child2,
            child3,
            subparent1,
                child4,
                child5,
               ]
    assert list(subparent1) == \
           [child4,
            child5,
            ]
    assert list(parent2) == \
           [subparent2,
                child6,
                child7,
            child1]
    assert list(subparent2) == \
           [child6,
            child7
            ]


def test_eq_contains_getitem_setitem():
    from tnode import TNode

    t = TNode()
    parent1 = TNode('parent1', parent=t)
    parent2 = TNode('parent2', parent=t)
    subparent2 = TNode('subparent2', parent=parent2)
    child6 = TNode('child6', parent=subparent2)
    child7 = TNode('child7', parent=subparent2)

    child1 = TNode('child1', parent=parent2)
    child2 = TNode('child2', parent=parent1)
    child3 = TNode('child3', parent=parent1)
    subparent1 = TNode('subparent1', parent=parent1)
    child4 = TNode('child4', parent=subparent1)
    child5 = TNode('child5', parent=subparent1)

    # ===== EQ =====
    assert parent1 == parent1
    assert parent1 == 'parent1'
    assert subparent2 == 'subparent2'
    assert subparent2 == 'parent2 > subparent2'
    assert child6 != child7
    assert child6 == 'child6'
    assert child6 == 'parent2 > subparent2 > child6'

    # ===== CONATAINS =====
    assert 'parent1' in t
    assert parent1 in t
    assert subparent2 in parent2
    assert 'subparent2' in parent2
    assert subparent2 in t
    assert 'subparent2' not in t
    assert 'parent2 > subparent2' in t
    assert 'child6' not in t
    assert 'child6' not in parent2
    assert 'child6' in subparent2
    assert 'subparent2 > child6' in parent2
    assert 'parent2 > subparent2 > child6' in t
    assert child6 in subparent2
    assert child6 in parent2
    assert child6 in t

    # ===== GETITEM =====
    assert t['parent1'] == parent1
    try:
        t['subparent2']
        raise AssertionError("Key error should have been raised!")
    except KeyError:
        pass
    assert t['parent2 > subparent2'] == subparent2
    try:
        t['child6']
        raise AssertionError("Key error should have been raised!")
    except KeyError:
        pass
    try:
        parent2['child6']
        raise AssertionError("Key error should have been raised!")
    except KeyError:
        pass
    assert subparent2['child6'] == child6
    assert parent2['subparent2 > child6'] == child6
    assert t['parent2 > subparent2 > child6'] == child6

    # ===== SETITEM =====
    t.clear()
    parent1.clear()
    parent2.clear()
    t['parent1'] = parent1
    assert t['parent1'] == parent1

    t['parent2'] = parent2
    assert t['parent2'] == parent2

    t['parent2 > subparent2'] = subparent2
    assert t['parent2 > subparent2'] == subparent2
    # subparent2 already had children
    assert t['parent2 > subparent2 > child6'] == child6

    # Create subparent1 automatically. This is needed for loading files.
    t['parent1 > subparent1 > child4'] = child4
    assert 'parent1 > subparent1' in t, 'Did not automaticall create subparent1'
    assert t['parent1 > subparent1 > child4'] == child4

    subparent2.clear()
    child6.title = ''
    parent2['subparent2 > child6'] = child6
    assert child6.title == 'child6'
    assert parent2['subparent2 > child6'] == child6

    # ===== Test new Title =====
    child6.title = 'new title'
    try:
        t['parent2 > subparent2 > child6']
        raise AssertionError('child6 should no longer be in subparent2 from re-title!')
    except KeyError:
        pass
    assert t['parent2 > subparent2 > new title'] == child6
    assert parent2['subparent2 > new title'] == child6


def test_str():
    from tnode import TNode

    t = TNode()
    parent1 = TNode('parent1', parent=t)
    parent2 = TNode('parent2', parent=t)
    subparent2 = TNode('subparent2', parent=parent2)
    child6 = TNode('child6', parent=subparent2)
    child7 = TNode('child7', parent=subparent2)

    child1 = TNode('child1', parent=parent2)
    child2 = TNode('child2', parent=parent1)
    child3 = TNode('child3', parent=parent1)
    subparent1 = TNode('subparent1', parent=parent1)
    child4 = TNode('child4', parent=subparent1)
    child5 = TNode('child5', parent=subparent1)

    assert str(t) == "TNode(full_title='')"
    assert str(parent1) == "TNode(full_title='parent1')"
    assert str(parent2) == "TNode(full_title='parent2')"
    assert str(subparent2) == "TNode(full_title='parent2 > subparent2')"
    assert str(child6) == "TNode(full_title='parent2 > subparent2 > child6')"
    assert str(child7) == "TNode(full_title='parent2 > subparent2 > child7')"


def test_to_dict_from_dict():
    from tnode import TNode

    t = TNode()
    parent1 = TNode('parent1', parent=t)
    parent2 = TNode('parent2', parent=t)
    subparent2 = TNode('subparent2', parent=parent2)
    child6 = TNode('child6', parent=subparent2)
    child7 = TNode('child7', parent=subparent2)

    child1 = TNode('child1', parent=parent2)

    child2 = TNode('child2', parent=parent1)
    child3 = TNode('child3', parent=parent1)
    subparent1 = TNode('subparent1', parent=parent1)
    child4 = TNode('child4', parent=subparent1)
    child5 = TNode('child5', parent=subparent1)

    assert t.to_dict() == {
        'title': '', 'children': [
            {'title': 'parent1',
             'children': [
                {'title': 'child2'},
                {'title': 'child3'},
                {'title': 'subparent1',
                 'children': [
                    {'title': 'child4'},
                    {'title': 'child5'},
                    ]}
                ]},
            {'title': 'parent2',
             'children': [
                {'title': 'subparent2',
                 'children': [
                    {'title': 'child6'},
                    {'title': 'child7'},
                    ]},
                {'title': 'child1'},
                ]},
            ]
        }

    t2 = TNode.from_dict(t.to_dict())
    assert t2.to_dict() == {
        'title': '', 'children': [
            {'title': 'parent1',
             'children': [
                {'title': 'child2'},
                {'title': 'child3'},
                {'title': 'subparent1',
                 'children': [
                    {'title': 'child4'},
                    {'title': 'child5'},
                    ]}
                ]},
            {'title': 'parent2',
             'children': [
                {'title': 'subparent2',
                 'children': [
                    {'title': 'child6'},
                    {'title': 'child7'},
                    ]},
                {'title': 'child1'},
                ]},
            ]
        }

    for v1, v2 in zip(t.iter(), t2.iter()):
        assert v1.full_title == v2.full_title


def test_json_support(remove_file=True):
    from tnode import TNode

    t = TNode()
    parent1 = TNode('parent1', parent=t)
    parent2 = TNode('parent2', parent=t)
    subparent2 = TNode('subparent2', parent=parent2)
    child6 = TNode('child6', parent=subparent2)
    child7 = TNode('child7', parent=subparent2)

    child1 = TNode('child1', parent=parent2)

    child2 = TNode('child2', parent=parent1)
    child3 = TNode('child3', parent=parent1)
    subparent1 = TNode('subparent1', parent=parent1)
    child4 = TNode('child4', parent=subparent1)
    child5 = TNode('child5', parent=subparent1)

    filename = 'test_json_support.json'
    try:
        fname = t.to_json(filename)
        assert fname == filename
        t2 = TNode.from_json(filename)

        assert t.to_dict() == t2.to_dict()
    finally:
        try:
            if remove_file:
                os.remove(filename)
        except (OSError, Exception):
            pass

    # Check that save/load works the same.
    try:
        fname = t.save(filename)
        assert fname == filename
        t2 = TNode.load(filename)

        assert t.to_dict() == t2.to_dict()
    finally:
        try:
            if remove_file:
                os.remove(filename)
        except (OSError, Exception):
            pass

    # Load into node
    try:
        fname = t.save(filename)
        assert fname == filename

        new_node = TNode(title='new node')
        new_node.load(filename)  # Overrides attribute title! {title: ''}

        assert t.to_dict() == new_node.to_dict()
    finally:
        try:
            if remove_file:
                os.remove(filename)
        except (OSError, Exception):
            pass

if __name__ == '__main__':
    test_init_and_properties()
    test_get_parents()
    test_add_child()
    test_remove_child()
    test_clear()
    test_find_parent()
    test_find()
    test_iter()
    test_eq_contains_getitem_setitem()
    test_str()
    test_to_dict_from_dict()
    test_json_support()
