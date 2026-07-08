import sys
import types
import importlib
from importlib.abc import MetaPathFinder, Loader
from importlib.machinery import ModuleSpec

class AliasLoader(Loader):
    def __init__(self, alias_target):
        self.alias_target = alias_target

    def create_module(self, spec):
        # Dynamically import the real module and return it
        return importlib.import_module(self.alias_target)

    def exec_module(self, module):
        # Executive phase is handled during importlib.import_module
        pass

class DynamicRedirectFinder(MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        # Redirect apps.bilgeapi to bilgeapi ONLY if bilgeapi exists as a top-level package
        if fullname == "apps.bilgeapi" or fullname.startswith("apps.bilgeapi."):
            if self._real_module_exists("bilgeapi"):
                redirected = fullname.replace("apps.bilgeapi", "bilgeapi", 1)
                return ModuleSpec(fullname, AliasLoader(redirected))
            return None
        
        # Redirect libs to bilgeapi.libs
        if fullname == "libs" or fullname.startswith("libs."):
            # Check if real libs exists first (so we don't interfere with monorepo)
            if self._real_module_exists(fullname):
                return None
            
            # Redirect to bilgeapi.libs ONLY if bilgeapi is a top-level package
            if self._real_module_exists("bilgeapi"):
                redirected = fullname.replace("libs", "bilgeapi.libs", 1)
                return ModuleSpec(fullname, AliasLoader(redirected))
        
        return None

    def _real_module_exists(self, fullname):
        # Temporarily remove ourselves to avoid infinite recursion
        if self in sys.meta_path:
            sys.meta_path.remove(self)
            try:
                # Use find_spec to check module existence without fully importing
                spec = importlib.util.find_spec(fullname)
                return spec is not None
            except Exception:
                return False
            finally:
                sys.meta_path.insert(0, self)
        return False

# Register the finder if not already registered
if not any(isinstance(f, DynamicRedirectFinder) for f in sys.meta_path):
    sys.meta_path.insert(0, DynamicRedirectFinder())

# Create dummy apps module in sys.modules so 'import apps' works ONLY if we are redirecting
if 'apps' not in sys.modules:
    # We only create the dummy apps if bilgeapi is a top-level package (standalone mode)
    # But wait, __init__.py runs when bilgeapi is imported.
    # We can check if 'apps' directory exists or if we should register the dummy.
    # To be safe, we can register the dummy if bilgeapi is importable top-level.
    # Let's check:
    finder = next(f for f in sys.meta_path if isinstance(f, DynamicRedirectFinder))
    if finder._real_module_exists("bilgeapi") and not finder._real_module_exists("apps"):
        apps = types.ModuleType('apps')
        apps.__path__ = []
        sys.modules['apps'] = apps
