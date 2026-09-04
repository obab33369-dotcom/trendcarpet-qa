import os
import json
import socket as _socket
from pathlib import Path

_real_connect = _socket.socket.connect

def _guarded_connect(self, address):
    host = address[0] if isinstance(address, tuple) else None
    if host not in ("127.0.0.1", "::1", "localhost", None):
        raise RuntimeError(f"REFORMA offline guard: blocked non-loopback connect to {host}")
    return _real_connect(self, address)

# Also guard socket.create_connection
if hasattr(_socket, 'create_connection'):
    _real_create_connection = _socket.create_connection
    def _guarded_create_connection(address, timeout=None, source_address=None):
        host = address[0] if isinstance(address, tuple) else None
        if host not in ("127.0.0.1", "::1", "localhost", None):
            raise RuntimeError(f"REFORMA offline guard: blocked non-loopback connect to {host}")
        if source_address:
            return _real_create_connection(address, timeout, source_address)
        return _real_create_connection(address, timeout)
    _socket.create_connection = _guarded_create_connection

def pytest_configure(config):
    # Register the online marker
    config.addinivalue_line("markers", "online: requires network/browser/Gemini")
    
    # Enable socket monkeypatching if offline mode is active
    if os.environ.get("REFORMA_OFFLINE") == "1":
        _socket.socket.connect = _guarded_connect
        if hasattr(_socket, 'create_connection'):
            _socket.create_connection = _guarded_create_connection

def pytest_collection_modifyitems(session, config, items):
    out_path_str = os.environ.get("REFORMA_NODEID_OUT")
    if not out_path_str:
        return
        
    node_ids = sorted({item.nodeid for item in items})
    out_path = Path(out_path_str)
    
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(node_ids, f, indent=2)
    except Exception as e:
        # Avoid crashing pytest collection if file output fails
        print(f"REFORMA offline guard error: failed to write nodeids: {e}")
