from typing import Any


class SubFunctions:

    async def call(
        self,
        params: dict[str, Any] | None = None,
        requests_args: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        raise NotImplementedError

    async def get_config(
        self, section: str | None = None, keyword: str | None = None
    ) -> dict[str, Any]:
        raise NotImplementedError

    async def set_special_config(
        self, section: str, items: dict[str, Any]
    ) -> dict[str, Any]:
        raise NotImplementedError

    async def delete_config(self, section: str, keyword: str) -> dict[str, Any]:
        raise NotImplementedError

    async def check_login(self) -> dict[str, Any] | bool:
        res = await self.get_config("servers")
        return res["config"] or False

    async def add_server(self, server: dict[str, Any]) -> dict[str, Any]:
        """server = {
            "name": "main",
            "displayname": "main",
            "host": "",
            "port": 5126,
            "timeout": 60,
            "username": "",
            "password": "",
            "connections": 8,
            "ssl": 1,
            "ssl_verify": 2,
            "ssl_ciphers": "",
            "enable": 1,
            "required": 0,
            "optional": 0,
            "retention": 0,
            "send_group": 0,
            "priority": 0,
        }"""
        return await self.set_special_config("servers", server)

    async def create_category(self, name: str, dir: str) -> dict[str, Any]:
        return await self.set_special_config("categories", {"name": name, "dir": dir})

    async def delete_category(self, name: str) -> dict[str, Any]:
        return await self.delete_config("categories", name)
