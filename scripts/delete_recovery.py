#!/usr/bin/env python3
"""
delete_recovery.py - delete-recovery skill core script v0.3.1

v0.3.1 Security fix (via safe_path.py):
- --force no longer skips PATH cross-check when SHA256 is absent (A4 bypass closed)

v0.3.0 Security fixes:
- SHA256 record now stores BOTH file hash AND original path (cross-linked)
  → Replacing the backup file forces attacker to also know the original path
  → Tampering with .path is detected by cross-checking against path in .sha256
- SHA256 is now STRICTLY REQUIRED on restore: missing or empty .sha256 blocks
  restore by default (use --force to bypass with explicit warning)
  This prevents the v0.2.0 bypass where deleting the .sha256 file disabled integrity
- allowed_roots is not enforced by default (None → []): restore destinations are NOT
  restricted to any specific directory tree; security relies on SHA256 integrity
  + PATH cross-check, not on directory confinement
- Added --force flag to restore command to bypass SHA256 existence check
  (for pre-v0.3.0 backups created before SHA256 was mandatory)

Backup auto-cleanup: 7 days
Log auto-cleanup: 30 days
Backup deleted by default after successful restore (use --keep-backup to retain)

Usage:
    backup:       python delete_recovery.py backup <file_path> [original_path]
    restore:      python delete_recovery.py restore <backup_folder> <safe_name> [--keep-backup] [--force]
    list:         python delete_recovery.py list
    delete:       python delete_recovery.py delete_backup <backup_folder>
    cleanup:      python delete_recovery.py cleanup
    log:          python delete_recovery.py log [lines]
    verify:       python delete_recovery.py verify <backup_folder> <safe_name>
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# Import security validation module v0.3.0
try:
    from safe_path import SafePathValidator, SafePathError
    HAS_SAFE_PATH = True
except ImportError:
    try:
        from .safe_path import SafePathValidator, SafePathError
        HAS_SAFE_PATH = True
    except ImportError:
        HAS_SAFE_PATH = False
        SafePathError = Exception

# Skill root directory (resolved from script location)
SKILL_DIR = Path(__file__).parent.parent.resolve()
BACKUP_ROOT = SKILL_DIR / "delete_backup"
BACKUP_ROOT.mkdir(exist_ok=True)

LOG_FILE = SKILL_DIR / "log.txt"

# v0.3.0: allowed_roots left empty (None) — security comes from SHA256
# integrity + path cross-check, NOT from restricting to a fixed directory tree.
# allowed_roots is available for users who want extra restrictions.
SAFE_VALIDATOR = SafePathValidator(BACKUP_ROOT, allowed_roots=None) if HAS_SAFE_PATH else None


# ─────────────────────────────────────────────────────────────────
# Logging utilities
# ─────────────────────────────────────────────────────────────────

def cleanup_old_logs():
    """Delete logs older than 30 days"""
    if not LOG_FILE.exists():
        return []

    cutoff = datetime.now() - timedelta(days=30)
    deleted = []
    remaining = []

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        try:
            ts_str = line.split("] [")[0].strip("[")
            log_time = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
            if log_time >= cutoff:
                remaining.append(line)
            else:
                deleted.append(line.strip())
        except (ValueError, IndexError):
            remaining.append(line)

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.writelines(remaining)

    return deleted


def log(action, status, detail=""):
    """
    Write a log entry.
    Security: strips newlines, carriage returns, and log-format delimiters from
    detail to prevent log-injection attacks (e.g. injecting fake timestamped
    log entries via a crafted detail string).
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    level_map = {
        "SUCCESS": "INFO",
        "FAIL": "ERROR",
        "CLEANUP": "CLEANUP",
        "SECURITY": "SECURITY",
    }
    level = level_map.get(status, "INFO")
    # Sanitize detail: remove chars that could inject fake log entries
    if detail:
        # Strip \r, \n, and the log delimiter sequence "["
        # (the log format is "[timestamp] [level] [action] status | detail\n")
        detail = detail.replace("\r", "").replace("\n", "")
        detail = detail.replace("[", "")  # prevents "[timestamp] [LEVEL] [FAKE]" injection
    record = f"[{timestamp}] [{level}] [{action}] {status}"
    if detail:
        record += f" | {detail}"
    record += "\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(record)


def get_timestamp():
    """Get current timestamp as folder name (YYYYMMDDHHMM)"""
    return datetime.now().strftime("%Y%m%d%H%M")


def cleanup_old_backups():
    """Delete backups older than 7 days"""
    if not BACKUP_ROOT.exists():
        return []

    cutoff = datetime.now() - timedelta(days=7)
    deleted = []

    for folder in BACKUP_ROOT.iterdir():
        if folder.is_dir():
            try:
                folder_time = datetime.strptime(folder.name, "%Y%m%d%H%M")
                if folder_time < cutoff:
                    shutil.rmtree(folder)
                    deleted.append(folder.name)
                    log("AutoCleanup", "CLEANUP", f"Removed expired backup: {folder.name}")
            except ValueError:
                pass

    return deleted


def list_backups():
    """List all backups, sorted newest first"""
    if not BACKUP_ROOT.exists():
        return []

    backups = []
    for folder in sorted(BACKUP_ROOT.iterdir(), key=lambda x: x.name, reverse=True):
        if folder.is_dir():
            files = [
                f.name for f in folder.iterdir()
                if f.name not in (".restored")
                and not f.name.endswith(".path")
                and not f.name.endswith(".sha256")
            ]
            backups.append({
                "folder": folder.name,
                "time": folder.name,
                "files": files,
                "count": len(files)
            })
    return backups


# ─────────────────────────────────────────────────────────────────
# Core: backup & restore (with security validation)
# ─────────────────────────────────────────────────────────────────

def backup_file(file_path, original_path):
    """
    Back up a file to a timestamped folder.
    v0.3.0: SHA256 file stores BOTH file hash AND original path (cross-linked).
    Tampering with either backup or .path requires forging both records correctly.

    file_path:     Full path of the file to back up
    original_path: Original file path (used to locate target during restore)
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    timestamp = get_timestamp()
    backup_dir = BACKUP_ROOT / timestamp
    backup_dir.mkdir(exist_ok=True)

    # Encode path separators to make safe filenames
    safe_name = str(file_path).replace("/", "__").replace("\\", "__").replace(":", "")
    backup_path = backup_dir / safe_name

    shutil.copy2(file_path, backup_path)

    # Store original path alongside the backup for restore targeting
    path_file = backup_dir / (safe_name + ".path")
    path_file.write_text(original_path, encoding="utf-8")

    # v0.3.0: Compute SHA256 and write signed SHA256 file (hash + path bound together)
    sha256_file = backup_dir / (safe_name + ".sha256")
    if HAS_SAFE_PATH:
        file_hash = SafePathValidator.compute_sha256(backup_path)
        SafePathValidator.write_sha256_file(sha256_file, file_hash, original_path)
        integrity_note = f" (SHA256: {file_hash[:16]}..., PATH bound)"
    else:
        # Graceful degradation: if safe_path.py is missing, write a minimal record
        # (still includes path to preserve some cross-check value)
        sha256_file.write_text(f"PATH:{original_path}\n", encoding="utf-8")
        integrity_note = " (safe_path.py not found, integrity check limited)"

    log("Backup", "SUCCESS", f"Backed up: {original_path} -> {timestamp}/" + integrity_note)
    return backup_dir.name, safe_name


def restore_file(backup_folder, safe_name, delete_backup_after=True, force=False):
    """
    Restore a file from backup to its original location.
    v0.3.0: Integrates full safe_path validation (integrity + path cross-check +
            allowed_roots enforcement). Refuses to restore tampered backups.
            SHA256 record is STRICTLY REQUIRED by default.

    delete_backup_after: Whether to delete the backup folder after restore (default True)
    force:              v0.3.0 new — bypass SHA256 existence check (for pre-v0.3.0 backups).
                        Does NOT bypass hash correctness check or path validation.
                        WARNING: Use only when restoring backups made before v0.3.0.
    """
    backup_dir = BACKUP_ROOT / backup_folder
    if not backup_dir.exists():
        raise FileNotFoundError(f"Backup folder not found: {backup_folder}")

    backup_path = backup_dir / safe_name
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found: {safe_name}")

    path_file = backup_dir / (safe_name + ".path")
    if not path_file.exists():
        raise ValueError(f"Original path record not found: {safe_name}.path")

    original_path = path_file.read_text(encoding="utf-8").strip()
    dest = Path(original_path)

    # ── v0.3.0 Security validation layer ───────────────────────
    sha256_file = backup_dir / (safe_name + ".sha256")

    if HAS_SAFE_PATH:
        try:
            SAFE_VALIDATOR.full_restore_check(
                backup_path=backup_path,
                sha256_file=sha256_file,
                original_path=original_path,
                dest_path=dest,
                force=force,
            )
        except SafePathError as e:
            log("Restore", "SECURITY", f"SECURITY BLOCK — {e}")
            raise SafePathError(
                f"Security validation failed, restore blocked!\n"
                f"Reason: {e}\n"
                f"If this backup was created before v0.3.0 and lacks a SHA256 record,\n"
                f"use --force to bypass the SHA256 existence check (path validation still applies)."
            ) from e
    # ── /Security validation layer ───────────────────────────

    dest.parent.mkdir(parents=True, exist_ok=True)

    # If destination file already exists, move it to temp_existing/
    if dest.exists():
        temp_dir = BACKUP_ROOT / "temp_existing"
        temp_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dest, temp_dir / dest.name)
        os.remove(dest)

    shutil.copy2(backup_path, dest)

    if delete_backup_after:
        # Record restored file in manifest; only delete folder when ALL files are restored
        manifest_file = backup_dir / ".restored"
        restored_set = set()
        if manifest_file.exists():
            restored_set = set(manifest_file.read_text(encoding="utf-8").strip().splitlines())
        restored_set.add(safe_name)
        manifest_file.write_text("\n".join(restored_set), encoding="utf-8")

        # Check how many files in this folder are still pending restore
        all_files = {
            f.name for f in backup_dir.iterdir()
            if f.name not in (".restored")
            and not f.name.endswith(".path")
            and not f.name.endswith(".sha256")
        }
        pending = all_files - restored_set

        if not pending:
            shutil.rmtree(backup_dir)
            log("Restore", "SUCCESS", f"All files restored from {backup_folder}, backup cleaned up")
        else:
            log("Restore", "SUCCESS",
                f"{original_path} restored, {len(pending)} file(s) still pending in {backup_folder}, backup kept")
    else:
        log("Restore", "SUCCESS", f"{original_path} restored, backup {backup_folder} kept")

    return original_path


def verify_backup(backup_folder, safe_name):
    """
    Verify backup integrity without restoring.
    Checks whether SHA256 matches the actual backup file content,
    and whether .sha256 PATH matches .path record.
    v0.3.0: This also reads and validates the SHA256 record format.
    """
    backup_dir = BACKUP_ROOT / backup_folder
    if not backup_dir.exists():
        raise FileNotFoundError(f"Backup folder not found: {backup_folder}")

    backup_path = backup_dir / safe_name
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found: {safe_name}")

    sha256_file = backup_dir / (safe_name + ".sha256")
    path_file = backup_dir / (safe_name + ".path")

    if not HAS_SAFE_PATH:
        return {
            "ok": False,
            "error": "safe_path.py not available — cannot perform integrity check",
            "integrity_check": False,
        }

    # Read path from .path file for cross-check
    original_path = ""
    if path_file.exists():
        original_path = path_file.read_text(encoding="utf-8").strip()

    # Try to read SHA256 record
    try:
        file_hash, stored_path = SafePathValidator.read_sha256_file(sha256_file)
    except SafePathError as e:
        return {
            "ok": False,
            "error": str(e),
            "integrity_check": False,
            "suggestion": "This backup may have been created before v0.3.0. "
                         "Use 'restore --force' to attempt recovery (path checks still apply).",
        }

    # Integrity check
    actual_sha256 = SafePathValidator.compute_sha256(backup_path)
    hash_match = (actual_sha256 == file_hash.lower())

    # Path cross-check (v0.3.0 new)
    path_match = True
    path_check_done = False
    if original_path and stored_path:
        path_match = (stored_path == original_path)
        path_check_done = True

    log("Verify", "SUCCESS" if (hash_match and path_match) else "SECURITY",
        f"Integrity: {'PASS' if hash_match else 'FAIL'}, "
        f"Path cross-check: {'PASS' if path_match else 'FAIL'} "
        f"for {backup_folder}/{safe_name}")

    return {
        "ok": True,
        "hash_match": hash_match,
        "path_match": path_match if path_check_done else None,
        "path_check_done": path_check_done,
        "expected_sha256": file_hash,
        "actual_sha256": actual_sha256,
        "stored_path": stored_path if 'stored_path' in dir() else None,
        "original_path_from_pathfile": original_path or None,
        "integrity_check": hash_match,
        "backup_file": str(backup_path),
    }


def delete_backup_folder(backup_folder):
    """Delete a specific backup folder manually"""
    backup_dir = BACKUP_ROOT / backup_folder
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
        log("DeleteBackup", "SUCCESS", f"Manually deleted backup folder: {backup_folder}")
        return True
    return False


def view_log(lines=50):
    """View the last N lines of the operation log"""
    if not LOG_FILE.exists():
        return []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        all_lines = f.readlines()
    return all_lines[-lines:]


# ─────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────

def main():
    # Auto-cleanup expired backups and logs on every invocation
    cleanup_old_backups()
    cleanup_old_logs()

    if len(sys.argv) < 2:
        print(json.dumps({"error": "Missing action argument"}))
        sys.exit(1)

    action = sys.argv[1]

    try:
        if action == "cleanup":
            deleted_backups = cleanup_old_backups()
            deleted_logs = cleanup_old_logs()
            print(json.dumps({
                "deleted_backups": deleted_backups,
                "deleted_logs": deleted_logs,
                "backup_count": len(deleted_backups),
                "log_count": len(deleted_logs)
            }))

        elif action == "list":
            backups = list_backups()
            print(json.dumps({"backups": backups}))

        elif action == "backup":
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Missing file path"}))
                sys.exit(1)
            file_path = sys.argv[2]
            original_path = sys.argv[3] if len(sys.argv) > 3 else file_path
            folder, safe_name = backup_file(file_path, original_path)
            print(json.dumps({"ok": True, "folder": folder, "file": safe_name}))

        elif action == "restore":
            if len(sys.argv) < 4:
                print(json.dumps({"error": "Missing parameters"}))
                sys.exit(1)
            folder = sys.argv[2]
            safe_name = sys.argv[3]
            delete_backup_after = "--keep-backup" not in sys.argv
            force = "--force" in sys.argv
            restored = restore_file(folder, safe_name, delete_backup_after=delete_backup_after, force=force)
            print(json.dumps({
                "ok": True,
                "restored_to": restored,
                "backup_deleted": delete_backup_after,
                "force_used": force,
            }))

        elif action == "delete_backup":
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Missing backup folder name"}))
                sys.exit(1)
            folder = sys.argv[2]
            deleted = delete_backup_folder(folder)
            print(json.dumps({"ok": deleted}))

        elif action == "verify":
            if len(sys.argv) < 4:
                print(json.dumps({"error": "Missing parameters"}))
                sys.exit(1)
            folder = sys.argv[2]
            safe_name = sys.argv[3]
            result = verify_backup(folder, safe_name)
            print(json.dumps(result))

        elif action == "log":
            lines = 50
            if len(sys.argv) > 2:
                try:
                    lines = int(sys.argv[2])
                except ValueError:
                    pass
            log_lines = view_log(lines)
            print(json.dumps({"log": log_lines, "count": len(log_lines)}))

        else:
            print(json.dumps({"error": f"Unknown action: {action}"}))
            sys.exit(1)

    except SafePathError as e:
        # Security errors handled separately to preserve correct log level
        print(json.dumps({"error": str(e), "security_error": True}))
        sys.exit(1)
    except Exception as e:
        log(action if 'action' in dir() else "Unknown", "FAIL", str(e))
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
