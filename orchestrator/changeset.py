import os
import re
import hashlib
from pathlib import Path
import logging

logger = logging.getLogger("orchestrator.changeset")

# NTFS reserved device names
RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
}

def get_file_sha256(file_path: Path) -> str:
    """
    Computes the SHA-256 hash of a file on disk.
    """
    if not file_path.exists():
        return ""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def canonicalize_path(wt_root: Path, relative_path: str) -> Path:
    """
    Safely resolves the path and prevents NTFS canonicalization/traversal attacks.
    """
    wt_root_resolved = wt_root.resolve()
    
    # 1. Basic path traversal protection
    target_path = Path(wt_root_resolved / relative_path)
    
    # On Windows, resolve() follows symlinks and resolves relative segments
    try:
        target_resolved = target_path.resolve()
    except Exception:
        # If the file does not exist, resolve its parent directory
        parent_resolved = target_path.parent.resolve()
        target_resolved = parent_resolved / target_path.name

    # 2. Containment check (guarantees the resolved path is inside the worktree)
    def _is_within(child: Path, parent: Path) -> bool:
        try:
            child.relative_to(parent)
            return True
        except ValueError:
            return False

    if not _is_within(target_resolved, wt_root_resolved):
        raise PermissionError(f"Security violation: Path {relative_path} traverses outside the worktree root.")

    # 3. Alternate Data Streams check (e.g. file.txt:stream)
    # The resolved path must not contain additional ':' colon characters beyond the drive specification (e.g., C:\)
    parts = list(target_resolved.parts)
    # The first part (drive letter) contains ':' on Windows. Rest of the parts shouldn't.
    for part in parts[1:]:
        if ":" in part:
            raise PermissionError(f"Security violation: Alternate Data Stream detected in path part '{part}'.")

    # 4. Check for reserved names case-insensitively
    for part in parts:
        name_without_ext = Path(part).stem.upper()
        if name_without_ext in RESERVED_NAMES:
            raise PermissionError(f"Security violation: Reserved Windows device name '{name_without_ext}' used in path.")

    # 5. Deny modification of critical directories and Windows 8.3 short name aliases
    forbidden_dirs = {".git", ".claude", ".github", ".reforma"}
    for part in parts:
        norm_part = part.rstrip(" .").lower()
        if norm_part in forbidden_dirs:
            raise PermissionError(f"Security violation: Direct mutation of critical directory '{part}' is denied.")
        if re.search(r"~\d", part):
            raise PermissionError(f"Security violation: 8.3 short-name alias detected in path part '{part}'.")

    return target_resolved

def validate_changeset(wt_root: Path, changeset: dict) -> list:
    """
    Validates a changeset before execution. Returns a list of resolved operations or raises exceptions.
    """
    resolved_ops = []
    
    # Track simulated filesystem state to support chained operations validation (e.g. rename A->B, then create A)
    simulated_exists = {}
    
    def path_exists(path: Path) -> bool:
        if path in simulated_exists:
            return simulated_exists[path]
        return path.exists()
    
    for op in changeset.get("operations", []):
        op_type = op.get("op")
        path_str = op.get("path")
        
        if not op_type or not path_str:
            raise ValueError("Invalid operation: missing 'op' or 'path' keys.")
            
        canonical_path = canonicalize_path(wt_root, path_str)
        
        if op_type == "modify":
            if not path_exists(canonical_path):
                raise FileNotFoundError(f"Cannot modify non-existent file: {path_str}")
            base_sha256 = op.get("base_sha256")
            if not base_sha256:
                raise ValueError(f"Missing base_sha256 for modify operation on {path_str}")
            
            # Optimistic Concurrency Control (OCC) check
            current_sha256 = get_file_sha256(canonical_path)
            if current_sha256 != base_sha256:
                raise RuntimeError(
                    f"Concurrency Conflict: File {path_str} has changed since Claude read it.\n"
                    f"Expected: {base_sha256}\nFound:    {current_sha256}"
                )
            
            resolved_ops.append({
                "op": "modify",
                "path": canonical_path,
                "proposed_content": op.get("proposed_content"),
                "eol": op.get("eol", "lf"),
                "encoding": op.get("encoding", "utf-8")
            })
            
        elif op_type == "create":
            if path_exists(canonical_path):
                raise FileExistsError(f"Cannot create file that already exists: {path_str}")
            resolved_ops.append({
                "op": "create",
                "path": canonical_path,
                "proposed_content": op.get("proposed_content"),
                "eol": op.get("eol", "lf"),
                "encoding": op.get("encoding", "utf-8")
            })
            simulated_exists[canonical_path] = True
            
        elif op_type == "delete":
            if not path_exists(canonical_path):
                raise FileNotFoundError(f"Cannot delete non-existent file: {path_str}")
            base_sha256 = op.get("base_sha256")
            if not base_sha256:
                raise ValueError(f"Missing base_sha256 for delete operation on {path_str}")
                
            current_sha256 = get_file_sha256(canonical_path)
            if current_sha256 != base_sha256:
                raise RuntimeError(f"Concurrency Conflict: File {path_str} was modified before deletion.")
                
            resolved_ops.append({
                "op": "delete",
                "path": canonical_path
            })
            simulated_exists[canonical_path] = False
            
        elif op_type == "rename":
            to_path_str = op.get("to")
            if not to_path_str:
                raise ValueError(f"Rename operation missing 'to' path for {path_str}")
            canonical_to = canonicalize_path(wt_root, to_path_str)
            if path_exists(canonical_to):
                raise FileExistsError(f"Rename target already exists: {to_path_str}")
            if not path_exists(canonical_path):
                raise FileNotFoundError(f"Rename source does not exist: {path_str}")
                
            resolved_ops.append({
                "op": "rename",
                "from": canonical_path,
                "to": canonical_to
            })
            simulated_exists[canonical_path] = False
            simulated_exists[canonical_to] = True
            
    return resolved_ops

def apply_changeset(wt_root: Path, changeset: dict) -> bool:
    """
    Validates and atomically applies a changeset to the task's worktree.
    All-or-nothing: if any validation fails, no files are modified.
    """
    logger.info(f"Applying changeset manifest for task {changeset.get('task_id')}")
    
    try:
        # 1. Validate all operations first (dry-run stage)
        resolved_ops = validate_changeset(wt_root, changeset)
        
        # 2. Apply all operations atomically
        for op in resolved_ops:
            op_type = op["op"]
            
            if op_type in ("modify", "create"):
                target_path = op["path"]
                content = op["proposed_content"] or ""
                eol = op["eol"]
                encoding = op["encoding"]
                
                # Normalize line endings
                if eol == "crlf":
                    content = content.replace("\n", "\r\n")
                else:
                    content = content.replace("\r\n", "\n")
                
                # Write atomically to a temp file, then swap
                temp_file = target_path.parent / (target_path.name + ".reforma-tmp")
                
                # Ensure parent directories exist
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(temp_file, "w", encoding=encoding, newline="") as f:
                    f.write(content)
                
                # Atomic replacement on Windows (replaces target whether or not it exists)
                import time
                for attempt in range(3):
                    try:
                        os.replace(temp_file, target_path)
                        break
                    except PermissionError as pe:
                        if attempt == 2:
                            raise pe
                        logger.warning(f"NTFS file lock collision on {target_path} during replace. Retrying in 0.5s...")
                        time.sleep(0.5)
                    
                logger.info(f"Successfully applied {op_type} on {target_path}")
                
            elif op_type == "delete":
                target_path = op["path"]
                target_path.unlink()
                logger.info(f"Successfully deleted {target_path}")
                
            elif op_type == "rename":
                from_path = op["from"]
                to_path = op["to"]
                to_path.parent.mkdir(parents=True, exist_ok=True)
                import time
                for attempt in range(3):
                    try:
                        from_path.rename(to_path)
                        break
                    except PermissionError as pe:
                        if attempt == 2:
                            raise pe
                        logger.warning(f"NTFS file lock collision on rename {from_path} to {to_path}. Retrying in 0.5s...")
                        time.sleep(0.5)
                logger.info(f"Successfully renamed {from_path} to {to_path}")
                
        return True
    except Exception as e:
        logger.error(f"Failed to apply changeset: {e}. Executing git rollback...")
        try:
            import subprocess
            subprocess.run(["git", "reset", "--hard"], cwd=str(wt_root), capture_output=True)
            subprocess.run(["git", "clean", "-fd"], cwd=str(wt_root), capture_output=True)
        except Exception as rollback_err:
            logger.error(f"Failed to rollback worktree: {rollback_err}")
        return False
