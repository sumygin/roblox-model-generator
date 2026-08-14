from mcp.server import Server, StdioServerTransport
from mcp.server.models import InitializationOptions
import subprocess
import mcp.types as types

server = Server("blender-roblox-mcp")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="convert_to_roblox_3d",
            description="Takes a raw AI-generated 3D model and uses Blender to optimize it for Roblox (decimates to <4000 triangles and exports as FBX).",
            inputSchema={
                "type": "object",
                "properties": {
                    "input_obj_path": {"type": "string"},
                    "output_fbx_path": {"type": "string"}
                },
                "required": ["input_obj_path", "output_fbx_path"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "convert_to_roblox_3d":
        input_path = arguments["input_obj_path"]
        output_path = arguments["output_fbx_path"]
        
        # Path to your Blender executable
        blender_path = "/Applications/Blender.app/Contents/MacOS/Blender" # Mac path
        # blender_path = "C:\\Program Files\\Blender Foundation\\Blender 4.0\\blender.exe" # Windows path
        
        # Run Blender in the background (headless)
        command = [
            blender_path,
            "--background",      # No UI
            "--python",          # Run a script
            "roblox_optimizer.py", 
            "--",                # Pass arguments to the script
            input_path,
            output_path
        ]
        
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            return [types.TextContent(type="text", text=f"Success! Model optimized for Roblox at: {output_path}")]
        except subprocess.CalledProcessError as e:
            return [types.TextContent(type="text", text=f"Blender failed: {e.stderr}")]

async def main():
    async with StdioServerTransport() as transport:
        await server.run(transport, InitializationOptions(
            server_name="blender-roblox-mcp",
            server_version="1.0"
        ), server.get_capabilities())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())