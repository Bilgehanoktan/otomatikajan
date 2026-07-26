import os
import subprocess
from pathlib import Path

def main():
    repo_root = Path(__file__).resolve().parents[1]
    
    # 1. Fetch Git metadata
    try:
        git_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd=repo_root,
            check=True
        ).stdout.strip()
        
        git_tag = subprocess.run(
            ["git", "describe", "--tags", "--always", "--dirty"],
            capture_output=True,
            text=True,
            cwd=repo_root,
            check=True
        ).stdout.strip()
    except Exception as e:
        print(f"[ERROR] Failed to get git metadata: {e}")
        return

    # 2. Update .env file
    env_path = repo_root / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        new_lines = []
        for line in lines:
            if line.startswith("BILGEAPI_GIT_SHA=") or line.startswith("BILGEAPI_GIT_TAG="):
                continue
            new_lines.append(line)
            
        new_lines.append(f"BILGEAPI_GIT_SHA={git_sha}\n")
        new_lines.append(f"BILGEAPI_GIT_TAG={git_tag}\n")
        
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"[OK] Injected Git metadata into .env: SHA={git_sha}, Tag={git_tag}")
    else:
        print("[WARNING] .env file not found. Skipping .env injection.")

    # 3. Write metadata files directly to the bilgeapi routers directory for Docker baking fallback
    routers_dir = repo_root / "apps" / "bilgeapi" / "routers"
    routers_dir.mkdir(parents=True, exist_ok=True)
    
    commit_file = routers_dir / ".git_commit"
    tag_file = routers_dir / ".git_tag"
    
    commit_file.write_text(git_sha, encoding="utf-8")
    tag_file.write_text(git_tag, encoding="utf-8")
    print(f"[OK] Wrote .git_commit and .git_tag files under {routers_dir}")

if __name__ == "__main__":
    main()
