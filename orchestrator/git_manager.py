import os
import sys
import subprocess
import shutil
import time
import logging
from pathlib import Path

# Windows specific imports for Job Objects
import win32job
import win32process
import win32api
import win32con

logger = logging.getLogger("orchestrator.git")

import threading
# Reentrant lock to prevent self-deadlocks on nested worktree helper calls
git_lock = threading.RLock()

# Short path for Windows worktrees to bypass 260 char path limit
WORKTREE_BASE_DIR = Path(r"C:\rf\wt")

def get_target_branch(repo_path: Path) -> str:
    """
    Detects the default/target branch of the repository.
    Returns 'master' for this repository by default, but checks symbolic refs if available.
    """
    try:
        res = subprocess.run(
            ["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
            cwd=str(repo_path),
            capture_output=True,
            text=True
        )
        if res.returncode == 0 and res.stdout.strip():
            ref = res.stdout.strip()
            if "/" in ref:
                return ref.split("/", 1)[1]
            return ref
    except Exception:
        pass
    
    try:
        res = subprocess.run(
            ["git", "branch", "--list", "main"],
            cwd=str(repo_path),
            capture_output=True,
            text=True
        )
        if "main" in res.stdout:
            return "main"
    except Exception:
        pass

    return "master"

def init_git_settings(repo_path: Path):
    """
    Enable Windows long path support in Git configuration for the repository.
    """
    try:
        subprocess.run(["git", "config", "core.longpaths", "true"], cwd=str(repo_path), check=True)
        subprocess.run(["git", "config", "gc.auto", "0"], cwd=str(repo_path), check=True)
        logger.info("Configured core.longpaths = true and gc.auto = 0 in git settings.")
    except Exception as e:
        logger.error(f"Failed to configure git settings: {e}")

def create_job_object():
    """
    Creates a Job Object configured to kill all child processes when the handle is closed.
    """
    h_job = win32job.CreateJobObject(None, "")
    extended_info = win32job.QueryInformationJobObject(h_job, win32job.JobObjectExtendedLimitInformation)
    # Set the limit flag to kill processes on handle close
    extended_info['BasicLimitInformation']['LimitFlags'] |= win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    win32job.SetInformationJobObject(h_job, win32job.JobObjectExtendedLimitInformation, extended_info)
    return h_job

def run_process_in_job(args: list, cwd: str, env: dict = None, stdout = None, stderr = None, stdin = None) -> subprocess.Popen:
    """
    Spawns a subprocess inside a Windows Job Object to guarantee process tree cleanup.
    Returns the Popen object. The caller must keep the job object handle open during execution.
    """
    h_job = create_job_object()
    env_block = env if env else os.environ.copy()
    
    # Use CREATE_NO_WINDOW to prevent spawning console windows that steal focus on Windows
    create_flags = 0x08000000  # CREATE_NO_WINDOW
    
    try:
        proc = subprocess.Popen(
            args,
            cwd=cwd,
            env=env_block,
            stdout=stdout,
            stderr=stderr,
            stdin=stdin,
            creationflags=create_flags
        )
    except Exception:
        win32api.CloseHandle(h_job)  # Prevent handle leak if spawn fails
        raise
        
    try:
        win32job.AssignProcessToJobObject(h_job, int(proc._handle))
    except Exception as e:
        logger.error(f"Failed to assign process to Job Object; killing process to avoid orphan: {e}")
        try:
            proc.kill()
        finally:
            win32api.CloseHandle(h_job)
        raise
        
    proc.h_job = h_job
    return proc

def create_worktree(repo_path: Path, task_id: str, base_commit: str) -> Path:
    r"""
    Creates a Git worktree for a task under C:\rf\wt\<task-id> on a task-specific branch.
    """
    with git_lock:
        init_git_settings(repo_path)
        
        branch_name = f"reforma/task/{task_id}"
        worktree_path = WORKTREE_BASE_DIR / task_id
        
        # Create worktree root directory parent if not exists
        WORKTREE_BASE_DIR.mkdir(parents=True, exist_ok=True)
        
        # If worktree directory already exists, clean it up first
        if worktree_path.exists():
            cleanup_worktree(repo_path, task_id)
            
        logger.info(f"Creating Git worktree at {worktree_path} for base commit {base_commit}")
        
        try:
            # Check if the branch already exists
            res = subprocess.run(["git", "show-ref", "--verify", f"refs/heads/{branch_name}"], cwd=str(repo_path), capture_output=True)
            if res.returncode == 0:
                # Branch exists, check out existing branch in worktree
                subprocess.run([
                    "git", "worktree", "add", str(worktree_path), branch_name
                ], cwd=str(repo_path), check=True)
            else:
                # Branch does not exist, create it from the base commit
                subprocess.run([
                    "git", "worktree", "add", "-b", branch_name, str(worktree_path), base_commit
                ], cwd=str(repo_path), check=True)
                
            # Exclude .claude/ folder from git tracking in this worktree
            try:
                git_dir_proc = subprocess.run(
                    ["git", "rev-parse", "--git-dir"],
                    cwd=str(worktree_path),
                    capture_output=True,
                    text=True,
                    check=True
                )
                git_dir = Path(git_dir_proc.stdout.strip())
                if not git_dir.is_absolute():
                    git_dir = worktree_path / git_dir
                exclude_file = git_dir / "info" / "exclude"
                exclude_file.parent.mkdir(parents=True, exist_ok=True)
                
                content = ""
                if exclude_file.exists():
                    content = exclude_file.read_text(encoding="utf-8")
                if ".claude/" not in content:
                    with open(exclude_file, "a", encoding="utf-8") as ef:
                        ef.write("\n.claude/\n")
                logger.info(f"Successfully configured exclude for .claude/ in {exclude_file}")
            except Exception as exc:
                logger.warning(f"Failed to exclude .claude/ in worktree: {exc}")
                
            logger.info(f"Successfully mounted worktree at {worktree_path}")
            return worktree_path
        except Exception as e:
            logger.error(f"Failed to create Git worktree: {e}")
            raise

def cleanup_worktree(repo_path: Path, task_id: str):
    """
    Cleans up the Git worktree and processes for a task.
    Enforces retry with backoff and process tree termination to prevent Windows file lock conflicts.
    """
    with git_lock:
        worktree_path = WORKTREE_BASE_DIR / task_id
        branch_name = f"reforma/task/{task_id}"
        
        logger.info(f"Cleaning up worktree and processes for task {task_id}")
        
        # 1. Remove Git worktree with retries
        for attempt in range(5):
            try:
                if worktree_path.exists():
                    subprocess.run([
                        "git", "worktree", "remove", "--force", str(worktree_path)
                    ], cwd=str(repo_path), check=True)
                break
            except Exception as e:
                logger.warning(f"Worktree remove attempt {attempt+1} failed: {e}. Retrying in 1s...")
                time.sleep(1.0)
                
        # Prune old worktree metadata in Git
        try:
            subprocess.run(["git", "worktree", "prune"], cwd=str(repo_path), check=True)
        except Exception:
            pass
            
        # Delete the branch
        try:
            subprocess.run(["git", "branch", "-D", branch_name], cwd=str(repo_path), capture_output=True)
        except Exception:
            pass
            
        # Clean directory if it lingers
        if worktree_path.exists():
            try:
                shutil.rmtree(worktree_path, ignore_errors=True)
            except Exception:
                pass

def rebase_and_verify(repo_path: Path, task_id: str, verify_func) -> str:
    """
    Rebases the task branch onto the target branch tip and runs verify_func inside the task worktree.
    Does NOT touch the checked-out branch in the primary repository.
    Returns: 'READY_FOR_REVIEW', 'CONFLICT', or 'VERIFY_FAILED'.
    """
    branch_name = f"reforma/task/{task_id}"
    worktree_path = WORKTREE_BASE_DIR / task_id
    
    logger.info(f"Initiating rebase and verify for task {task_id}")
    
    with git_lock:
        target = get_target_branch(repo_path)
        
        # 1. Fetch latest changes
        try:
            subprocess.run(["git", "fetch", "origin", target], cwd=str(repo_path), capture_output=True)
        except Exception:
            pass
            
        # 2. Get target branch tip commit
        res_tip = subprocess.run(["git", "rev-parse", target], cwd=str(repo_path), capture_output=True, text=True)
        if res_tip.returncode != 0:
            logger.error(f"Failed to find tip of target branch {target}")
            return "VERIFY_FAILED"
        target_tip = res_tip.stdout.strip()
        
        # 3. Perform rebase in the task worktree
        logger.info(f"Rebasing worktree branch {branch_name} onto {target} ({target_tip})")
        res_rebase = subprocess.run(
            ["git", "-C", str(worktree_path), "rebase", target],
            cwd=str(repo_path),
            capture_output=True,
            text=True
        )
        
        if res_rebase.returncode != 0:
            logger.error(f"Rebase conflict for task {task_id}. Aborting rebase.\nError: {res_rebase.stderr}")
            subprocess.run(["git", "-C", str(worktree_path), "rebase", "--abort"], cwd=str(repo_path), capture_output=True)
            return "CONFLICT"
            
        # 4. Run the verify function inside the task worktree
        try:
            verified = verify_func(worktree_path)
            if not verified:
                logger.error(f"Verification failed after rebase for task {task_id}")
                return "VERIFY_FAILED"
            
            logger.info(f"Verification passed after rebase. Task {task_id} is READY_FOR_REVIEW.")
            return "READY_FOR_REVIEW"
        except Exception as e:
            logger.exception(f"Exception during verify sequence: {e}")
            return "VERIFY_FAILED"
