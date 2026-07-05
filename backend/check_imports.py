import sys
import os
import importlib.util

def check_files():
    base = os.path.abspath("app")
    for root, dirs, files in os.walk(base):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                module_name = "app." + os.path.relpath(path, base).replace("/", ".").replace(".py", "")
                if module_name.endswith(".__init__"):
                    module_name = module_name[:-9]

                try:
                    spec = importlib.util.spec_from_file_location(module_name, path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                except Exception as e:
                    print(f"Error in {path}: {e}")

check_files()
