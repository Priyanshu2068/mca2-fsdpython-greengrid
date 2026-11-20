#!/usr/bin/env python
"""
GreenGrid root manage.py convenience wrapper.
Allows running Django commands directly from repository root.
"""
import os
import sys

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(root_dir, 'backend')
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
        execute_from_command_line(sys.argv)
    except (ImportError, ModuleNotFoundError) as exc:
        sys.stderr.write(
            "\n"
            "=========================================================================\n"
            "GreenGrid Virtual Environment Warning:\n"
            f"Failed to load dependency: {exc}\n\n"
            "You are running with system Python instead of the GreenGrid virtual environment.\n"
            "Please run using the project virtual environment:\n\n"
            "  Direct Command:  .\\venv\\Scripts\\python.exe manage.py runserver\n"
            "  Or Activate venv: .\\venv\\Scripts\\activate ; python manage.py runserver\n"
            "=========================================================================\n\n"
        )
        sys.exit(1)

if __name__ == '__main__':
    main()