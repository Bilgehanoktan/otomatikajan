import os
import shutil

def clean():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    print(f"Cleaning release residues in root: {root_dir}")

    package_dir = os.path.join(root_dir, "apps", "bilgeapi")
    print(f"Cleaning release residues in package: {package_dir}")

    dir_names = [
        "__pycache__",
        ".pytest_cache",
        "bilgeapi.egg-info",
        "build",
        "dist",
        "runtime",
        "tmp",
    ]

    for target in [root_dir, package_dir]:
        if not os.path.exists(target):
            continue
        for root, dirs, files in os.walk(target, topdown=False):
            if ".git" in root or ".legacy_archive" in root:
                continue
            for name in dirs:
                if name in dir_names or name.endswith(".egg-info") or name == "__pycache__":
                    dir_path = os.path.join(root, name)
                    print(f"Removing directory: {dir_path}")
                    try:
                        shutil.rmtree(dir_path)
                    except Exception as e:
                        print(f"Failed to remove directory {dir_path}: {e}")

            for file in files:
                file_path = os.path.join(root, file)
                is_residue = False
                if file.endswith(".db") or file.endswith(".log") or file == ".coverage" or file == "coverage.xml" or file.endswith(".pyc"):
                    is_residue = True
                
                if is_residue:
                    print(f"Removing file: {file_path}")
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f"Failed to remove file {file_path}: {e}")

    print("Cleanup completed successfully.")

if __name__ == "__main__":
    clean()
