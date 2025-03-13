from typing import Dict, Tuple, Optional, Any, Hashable

from fastapi import WebSocket


class WebSocketManager:
    class WebSocketManagerGroup:
        def __init__(
                self,
                name: Optional[Hashable] = None,
                parent: Optional["WebSocketManager.WebSocketManagerGroup"] = None,
        ):
            """
            WebSocket 管理器分组

            参数:
            - name: 分组名称
            - parent: 父分组

            属性:
            - name: 分组名称
            - parent: 父分组
            - children: 子分组
            - connections: WebSocket 连接
            """
            self.name: Optional[Hashable] = name
            self.parent: Optional[WebSocketManager.WebSocketManagerGroup] = parent
            self.children: Dict[Hashable, WebSocketManager.WebSocketManagerGroup] = dict()
            self.connections: Dict[Hashable, WebSocket] = dict()

        def has_child(
                self,
                key: Hashable,
        ):
            return key in self.children

        def get_child(
                self,
                key: Hashable,
        ):
            return self.children[key]

        def add_child(
                self,
                key: Hashable,
                value: "WebSocketManager.WebSocketManagerGroup",
        ):
            self.children[key] = value

        def remove_child(
                self,
                key: Hashable,
        ):
            del self.children[key]

        def add_connection(
                self,
                identifier: Hashable,
                websocket: WebSocket,
        ):
            """
            添加 WebSocket 连接

            参数:
            - identifier: WebSocket 连接的标识符
            - websocket: WebSocket 对象

            异常:
            - RuntimeError: 当 WebSocket 连接已存在时抛出
            """
            if identifier in self.connections:
                raise RuntimeError(f"WebSocket connection with identifier: {identifier} already exists")
            self.connections[identifier] = websocket

        def remove_connection(
                self,
                identifier: Hashable,
        ) -> WebSocket:
            """
            移除 WebSocket 连接

            参数:
            - identifier: WebSocket 连接的标识符

            返回:
            - 移除的 WebSocket 对象
            """
            if identifier not in self.connections:
                raise RuntimeError(f"WebSocket connection with identifier: {identifier} not found")
            connection = self.connections[identifier]
            del self.connections[identifier]
            return connection

    def __init__(self):
        self.groups = WebSocketManager.WebSocketManagerGroup()

    def add(
            self,
            keys: Tuple[Hashable, ...],
            identifier: Hashable,
            websocket: WebSocket,
    ):
        """
        添加 WebSocket 连接到管理器

        参数:
        - keys: WebSocket 分组的键
        - identifier: WebSocket 连接的标识符
        - websocket: WebSocket 对象
        """
        current = self.groups
        for key in keys:
            if current.has_child(key):
                current = current.get_child(key)
            else:
                current.add_child(key, WebSocketManager.WebSocketManagerGroup(key, current))
                current = current.get_child(key)
        current.add_connection(identifier, websocket)

    def remove(
            self,
            keys: Tuple[Hashable, ...],
            identifier: Hashable,
    ) -> WebSocket:
        """
        移除 WebSocket 连接

        参数:
        - keys: WebSocket 分组的键
        - identifier: WebSocket 连接的标识符

        返回:
        - 移除的 WebSocket 对象
        """
        current = self.groups
        for key in keys:
            if not current.has_child(key):
                raise RuntimeError(f"WebSocket group with keys: {keys} not found")
            current = current.get_child(key)
        connection = current.remove_connection(identifier)
        while current and not current.connections and not current.children:
            current.parent.remove_child(current.name)
            current = current.parent
        return connection

    def group(
            self,
            keys: Tuple[Hashable, ...],
    ) -> WebSocketManagerGroup:
        """
        获取 WebSocket 分组

        参数:
        - keys: WebSocket 分组的键

        返回:
        - WebSocket 分组
        """
        current = self.groups
        for key in keys:
            if not current.has_child(key):
                raise RuntimeError(f"WebSocket group with keys: {keys} not found")
            current = current.get_child(key)
        return current

    async def broadcast_json(
            self,
            keys: Tuple[Hashable, ...],
            content: Any,
    ):
        """
        广播 JSON 内容

        参数:
        - keys: WebSocket 分组的键
        - content: JSON 内容
        """
        node = self.group(keys)
        for conn in node.connections.values():
            await conn.send_json(content)
