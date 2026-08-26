# data_structures.py
from __future__ import annotations
from typing import Any, Optional, List, Generic, TypeVar
from dataclasses import dataclass

T = TypeVar("T")


# ---------- Stack (for recent question history) ----------

class Stack(Generic[T]):
    def __init__(self) -> None:
        self._items: List[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> Optional[T]:
        if not self._items:
            return None
        return self._items.pop()

    def peek(self) -> Optional[T]:
        if not self._items:
            return None
        return self._items[-1]

    def is_empty(self) -> bool:
        return len(self._items) == 0

    def size(self) -> int:
        return len(self._items)

    def to_list(self) -> List[T]:
        # Return a copy so external code cannot mutate internal state
        return list(self._items)


# ---------- Queue (for unanswered queries) ----------

class Queue(Generic[T]):
    def __init__(self) -> None:
        self._items: List[T] = []

    def enqueue(self, item: T) -> None:
        self._items.append(item)

    def dequeue(self) -> Optional[T]:
        if not self._items:
            return None
        return self._items.pop(0)

    def front(self) -> Optional[T]:
        if not self._items:
            return None
        return self._items[0]

    def is_empty(self) -> bool:
        return len(self._items) == 0

    def size(self) -> int:
        return len(self._items)

    def to_list(self) -> List[T]:
        return list(self._items)


# ---------- Linked List (for dynamic FAQ list) ----------

@dataclass
class Node(Generic[T]):
    data: T
    next: Optional[Node[T]] = None


class LinkedList(Generic[T]):
    def __init__(self) -> None:
        self.head: Optional[Node[T]] = None
        self._size: int = 0

    def append(self, data: T) -> None:
        new_node = Node(data)
        if not self.head:
            self.head = new_node
            self._size += 1
            return

        current = self.head
        while current.next:
            current = current.next
        current.next = new_node
        self._size += 1

    def insert_at(self, index: int, data: T) -> bool:
        if index < 0 or index > self._size:
            return False

        new_node = Node(data)
        if index == 0:
            new_node.next = self.head
            self.head = new_node
            self._size += 1
            return True

        current = self.head
        for _ in range(index - 1):
            current = current.next  # type: ignore

        new_node.next = current.next  # type: ignore
        current.next = new_node  # type: ignore
        self._size += 1
        return True

    def delete_at(self, index: int) -> bool:
        if index < 0 or index >= self._size:
            return False

        if index == 0:
            self.head = self.head.next if self.head else None
            self._size -= 1
            return True

        current = self.head
        for _ in range(index - 1):
            current = current.next  # type: ignore

        if current.next:  # type: ignore
            current.next = current.next.next  # type: ignore
            self._size -= 1
            return True
        return False

    def get_at(self, index: int) -> Optional[T]:
        if index < 0 or index >= self._size:
            return None

        current = self.head
        for _ in range(index):
            current = current.next  # type: ignore
        return current.data if current else None

    def size(self) -> int:
        return self._size

    def to_list(self) -> List[T]:
        result: List[T] = []
        current = self.head
        while current:
            result.append(current.data)
            current = current.next
        return result


# ---------- Binary Search Tree (for category-organized info) ----------

@dataclass
class TreeNode(Generic[T]):
    key: str
    value: T
    left: Optional[TreeNode[T]] = None
    right: Optional[TreeNode[T]] = None


class BinarySearchTree(Generic[T]):
    def __init__(self) -> None:
        self.root: Optional[TreeNode[T]] = None

    def insert(self, key: str, value: T) -> None:
        if not self.root:
            self.root = TreeNode(key, value)
            return

        current = self.root
        while True:
            if key < current.key:
                if current.left is None:
                    current.left = TreeNode(key, value)
                    return
                current = current.left
            elif key > current.key:
                if current.right is None:
                    current.right = TreeNode(key, value)
                    return
                current = current.right
            else:
                # Key exists; update value
                current.value = value
                return

    def search(self, key: str) -> Optional[T]:
        current = self.root
        while current:
            if key == current.key:
                return current.value
            elif key < current.key:
                current = current.left
            else:
                current = current.right
        return None

    def delete(self, key: str) -> bool:
        # Simple implementation: rebuild tree without the key
        nodes = self.inorder_traversal()
        filtered = [(k, v) for k, v in nodes if k != key]
        if len(filtered) == len(nodes):
            return False  # Key not found

        self.root = None
        for k, v in filtered:
            self.insert(k, v)
        return True

    def inorder_traversal(self) -> List[tuple[str, T]]:
        result: List[tuple[str, T]] = []

        def _inorder(node: Optional[TreeNode[T]]) -> None:
            if not node:
                return
            _inorder(node.left)
            result.append((node.key, node.value))
            _inorder(node.right)

        _inorder(self.root)
        return result

    def is_empty(self) -> bool:
        return self.root is None