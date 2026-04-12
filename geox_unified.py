"""
Legacy Entrypoint Shim.
The actual VPS execution plane server has moved to execution_plane/vps/server.py.
"""
from execution_plane.vps.server import main
if __name__ == "__main__":
    main()
