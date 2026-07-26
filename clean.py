#!/usr/bin/env python
import os
import shutil
import sys

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Starting cleanup from root: {root_dir}")

    # Folders to delete recursively
    folders_to_delete = {
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "htmlcov",
        "build",
        "dist",
    }

    # File extensions to delete recursively
    extensions_to_delete = {
        ".pyc",
        ".pyo",
        ".pyd",
    }

    # Specific database/log files to delete
    specific_files_to_delete = {
        "cortex_local_v2.db",
        "governance_test.db",
        ".coverage",
        "pytest_output.txt",
        "backend.log",
        "backend_debug.log",
        "backend_err.log",
        "backend_error.log",
        "backend_test.log",
        "live_backend.log",
        "live_backend_phase32.err.log",
        "live_backend_phase32.out.log",
        "live_backend_v2.log",
        "live_backend_v3.log",
        "live_backend_v4.log",
        "live_frontend.err.log",
        "live_frontend.log",
        "live_worker.log",
        "live_worker_v2.log",
        "worker_tail.log",
        "worker_tail_utf8.log",
        "startup_log.txt",
        "build_log.txt",
        "lint_output.txt",
        "pytest_full_tb.txt",
        "pytest_output.txt",
        "pytest_output_v2.txt",
        "pytest_output_v3.txt",
        "pytest_output_v4.txt",
        "pytest_output_v5.txt",
        "pytest_output_v6.txt",
        "pytest_output_v7.txt",
        "pytest_output_v8.txt",
        "pytest_output_v9.txt",
        "pytest_output_v10.txt",
        "pytest_output_v11.txt",
        "pytest_output_v12.txt",
        "pytest_output_v13.txt",
    }

    # Specific directories to clear contents of (retaining the dir itself)
    directories_to_clear = [
        os.path.join(root_dir, ".bilgeapi", "audit"),
        os.path.join(root_dir, ".bilgeapi", "memory"),
        os.path.join(root_dir, ".bilgeapi", "logs"),
        os.path.join(root_dir, ".bilgeapi", "reports"),
        os.path.join(root_dir, ".bilgeapi", "quarantine"),
        os.path.join(root_dir, "runtime", "data"),
        os.path.join(root_dir, "runtime", "test_workspace", "memory"),
        os.path.join(root_dir, "runtime", "test_workspace", "logs"),
    ]

    deleted_folders_count = 0
    deleted_files_count = 0

    # Walk the tree
    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=False):
        # Prevent walking into .venv, .pydeps314, .backup, node_modules, or .git to avoid scanning too many files
        parts = set(dirpath.split(os.sep))
        if any(ignored in parts for ignored in {".venv", ".pydeps314", ".backup", "node_modules", ".git"}):
            continue

        # 1. Delete matching files
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            ext = os.path.splitext(filename)[1].lower()
            
            should_delete = (
                ext in extensions_to_delete or
                filename in specific_files_to_delete or
                filename.startswith(".coverage.")
            )

            if should_delete:
                try:
                    os.remove(file_path)
                    deleted_files_count += 1
                except Exception as e:
                    print(f"Error removing file {file_path}: {e}")

        # 2. Delete matching folders
        for dirname in list(dirnames):
            folder_path = os.path.join(dirpath, dirname)
            should_delete = (
                dirname in folders_to_delete or
                dirname.endswith(".egg-info")
            )

            if should_delete:
                try:
                    shutil.rmtree(folder_path)
                    dirnames.remove(dirname)
                    deleted_folders_count += 1
                except Exception as e:
                    print(f"Error removing folder {folder_path}: {e}")

    # 3. Clear contents of specific directories
    for target_dir in directories_to_clear:
        if os.path.exists(target_dir):
            for item in os.listdir(target_dir):
                item_path = os.path.join(target_dir, item)
                try:
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                        deleted_folders_count += 1
                    else:
                        os.remove(item_path)
                        deleted_files_count += 1
                except Exception as e:
                    print(f"Error clearing {item_path} inside {target_dir}: {e}")

    print(f"Cleanup finished successfully.")
    print(f"Deleted {deleted_folders_count} directories and {deleted_files_count} files.")

if __name__ == "__main__":
    main()
