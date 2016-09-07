import sys

def import_module_from_file(name, path):
    """Imports a module from a file path. Implements different methods based
    on Python version."""

    py_version = sys.version_info[:2]

    if py_version >= (3, 5):
        import importlib.util
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    elif (3, 3) <= py_version <= (3, 4):
        from importlib.machinery import SourceFileLoader
        mod = SourceFileLoader(name, path).load_module()
    else:
        import imp
        mod = imp.load_source(name, path)
    return mod
