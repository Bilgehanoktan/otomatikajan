import json
import os
import sys
from pathlib import Path

# Add project root directory to python path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from bilgeapi.main import app

def export_openapi():
    # Compile schema structure
    openapi_schema = app.openapi()
    
    # Define output directory and file
    output_dir = ROOT_DIR / "docs" / "openapi"
    os.makedirs(output_dir, exist_ok=True)
    output_path = output_dir / "bilgeapi_openapi.json"
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully exported OpenAPI schema to: {output_path}")

if __name__ == "__main__":
    export_openapi()
