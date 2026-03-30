import threading
import time

from fastmcp import FastMCP


class BackgroundMCPServer:
    def __init__(self):
        self.mcp = FastMCP("background-server")
        self._register_tools()
        self.thread = threading.Thread(target=self.mcp.run, daemon=True, args=["http", False])
        self.thread.start()

    def _register_tools(self):
        @self.mcp.tool()
        async def add_numbers(a: int, b: int) -> int:
            return a + b

        @self.mcp.tool()
        async def reverse_text(text: str) -> str:
            return text[::-1]

        @self.mcp.tool()
        async def simulate_heavy_task(seconds: int) -> str:
            await time.sleep(seconds)
            return f"Task completed after {seconds} seconds"
