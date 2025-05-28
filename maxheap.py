# Max Binary Heap
def _Item_init(k, v):
    """Lightweight composite to store priority queue items."""
    return (k,v)

def _Item_gt(x, y):
    """Compare items based on their keys (for max heap)."""
    return x[0] > y[0]

def is_empty(heap):
    """Return True if the priority queue is empty."""
    return len(heap) == 0

def _parent(j):
    return (j - 1) // 2

def _left(j):
    return 2*j + 1

def _right(j):
    return 2*j + 2

def _has_left(heap, j):
    return _left(j) < len(heap)

def _has_right(heap, j):
    return _right(j) < len(heap)

def _swap(heap, i, j):
    """Swap the elements at indices i and j of array."""
    heap[i], heap[j] = heap[j], heap[i]

def _upheap(heap, j):
    """Move the item at index j up to its proper position in the heap."""
    parent = _parent(j)
    if j > 0 and _Item_gt(heap[j], heap[parent]):
        _swap(heap, j, parent)
        _upheap(heap, parent)

def _downheap(heap, j):
    """Move the item at index j down to its proper position in the heap."""
    if _has_left(heap, j):
        left = _left(j)
        large_child = left
        if _has_right(heap, j):
            right = _right(j)
            if _Item_gt(heap[right], heap[left]):
                large_child = right
        if _Item_gt(heap[large_child], heap[j]):
            _swap(heap, j, large_child)
            _downheap(heap, large_child)

def _heapify(heap):
    n = len(heap)
    start = _parent(n - 1)
    for i in range(start, -1, -1):
        _downheap(heap, i)

# Priority Queue using max heap
def create_heap_priority_queue():
    """Create a new empty Priority Queue (as a list)."""
    return []

def __len__(heap):
    """Return the number of items in the priority queue."""
    return len(heap)

def add(heap, key, value):
    """Add a key-value pair to the priority queue."""
    heap.append(_Item_init(key, value))
    _upheap(heap, len(heap) - 1)

def max(heap):
    """Return but do not remove (k,v) pair with maximum key."""
    if is_empty(heap):
        return "Priority queue is empty."
    item = heap[0]
    return (item[0], item[1])

def peek_max(heap):
    return heap[0]

def remove_max(heap):
    """Remove and return (k,v) pair with maximum key."""
    if is_empty(heap):
        return "Priority queue is empty."
    _swap(heap, 0, len(heap) - 1)   # put maximum item at the end
    item = heap.pop()               # remove it from the list
    if not is_empty(heap):
        _downheap(heap, 0)         # fix new root
    return (item[0], item[1])

def remove(heap, value):
    """Remove the item with the specified value from the priority queue."""
    if is_empty(heap):
        return "Priority queue is empty."
    item = None
    for i in range(len(heap)):
        if heap[i][1] == value:
            last = len(heap) - 1
            _swap(heap, i, last)
            item = heap.pop()
            break
    if not is_empty(heap):
        _heapify(heap)

    if item is not None:
        return (item[0], item[1])
    else:
        return "Value not found"

def update_priority(heap, value, new_key):
    """Update priority of item with given value."""
    if is_empty(heap):
        return False
    found_index = -1
    for i in range(len(heap)):
        if heap[i][1] == value:
            found_index = i
            break
    if found_index == -1:
        return False
    old_key = heap[found_index][0]
    heap[found_index] = _Item_init(new_key, value)
    if new_key > old_key:
        _upheap(heap, found_index)
    else:
        _downheap(heap, found_index)
    return True

# Testing

def test_create_heap_priority_queue():
    """Test creation of an empty priority queue."""
    heap = create_heap_priority_queue()
    assert isinstance(heap, list), "The priority queue should be a list."
    assert len(heap) == 0, "New priority queue should have length 0."
    print(heap)

def test_is_empty_and_len():
    """Test is_empty and __len__ functions."""
    heap = create_heap_priority_queue()
    # Initially empty
    assert is_empty(heap) is True, "Queue should be empty upon creation."
    assert __len__(heap) == 0, "Length should be 0 upon creation."
    # After adding an element
    add(heap, 10, "a")
    print(heap)
    assert is_empty(heap) is False, "Queue should not be empty after one insertion."
    assert __len__(heap) == 1, "Length should be 1 after one insertion."

def test_add_and_max():
    """Test adding items and retrieving the maximum element."""
    heap = create_heap_priority_queue()
    add(heap, 5, "a")
    add(heap, 3, "b")
    add(heap, 4, "c")
    add(heap, 1, "d")
    add(heap, 2, "e")
    print(heap, 1)
    update_priority(heap, "b", 2)
    print(heap, 2)
    # The maximum key should be 5 with value "a"
    result = max(heap)
    assert result == (5, "a"), f"Expected max to return (5, 'a'), but got {result}"

def test_remove_max():
    """Test removal of the maximum element and the overall removal order."""
    heap = create_heap_priority_queue()
    add(heap, 5, "a")
    add(heap, 3, "b")
    add(heap, 4, "c")
    
    # Remove the maximum element; should be (5, "a")
    result1 = remove_max(heap)
    assert result1 == (5, "a"), f"Expected remove_max to return (5, 'a'), but got {result1}"
    
    # Now the remaining keys are 3 and 4; the new max should be (4, "c")
    result2 = max(heap)
    assert result2 == (4, "c"), f"Expected max to return (4, 'c') after removal, but got {result2}"
    
    # Continue removals:
    result3 = remove_max(heap)
    assert result3 == (4, "c"), f"Expected remove_max to return (4, 'c'), but got {result3}"
    
    result4 = remove_max(heap)
    assert result4 == (3, "b"), f"Expected remove_max to return (3, 'b'), but got {result4}"
    
    # Now the heap should be empty
    assert is_empty(heap) is True, "Queue should be empty after all removals."
    # Calling remove_max on an empty queue should return the error message.
    result_empty = remove_max(heap)
    assert result_empty == "Priority queue is empty.", f"Expected error message on removal from empty queue, got {result_empty}"

def test_remove_key():
    """Test removal of a specific key from the priority queue."""
    heap = create_heap_priority_queue()
    add(heap, 6, "a")
    add(heap, 5, "b")
    add(heap, 1, "c")
    add(heap, 3, "d")
    add(heap, 2, "e")
    add(heap, 4, 'f')
    
    # Remove the item with key 4
    print(heap)
    result = remove(heap, 4)
    print(heap)
    assert result == (4, "f"), f"Expected remove to return (4, 'c'), but got {result}"
    
    # Check if the item is removed
    assert remove(heap, 4) == "Key not found", "Expected error message for non-existing key."

def test_max_empty():
    """Test that calling max on an empty priority queue returns the error message."""
    heap = create_heap_priority_queue()
    result = max(heap)
    assert result == "Priority queue is empty.", f"Expected max() on empty queue to return error message, but got {result}"

def run_all_tests():
    test_create_heap_priority_queue()
    test_is_empty_and_len()
    test_add_and_max()
    test_remove_max()
    test_remove_key()
    test_max_empty()
    print("All tests passed!")

if __name__ == '__main__':
    run_all_tests()