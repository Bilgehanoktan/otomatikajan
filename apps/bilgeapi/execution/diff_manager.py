import difflib
from typing import Optional
from apps.bilgeapi.security.secret_scanner import SecretScanner

class DiffManager:
    def __init__(self, secret_scanner: Optional[SecretScanner] = None):
        self.secret_scanner = secret_scanner or SecretScanner()

    def generate_diff(self, filepath: str, original_content: str, modified_content: str) -> str:
        """
        Generates a standard unified diff between original and modified content.
        Runs SecretScanner on both contents before generating the diff.
        """
        clean_orig = self.secret_scanner.scan_and_mask(original_content)
        clean_mod = self.secret_scanner.scan_and_mask(modified_content)

        orig_lines = clean_orig.splitlines(keepends=True)
        mod_lines = clean_mod.splitlines(keepends=True)

        diff = difflib.unified_diff(
            orig_lines,
            mod_lines,
            fromfile=f"a/{filepath}",
            tofile=f"b/{filepath}"
        )
        return "".join(diff)
