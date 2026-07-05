import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from truthlens import create_app
from truthlens.bootstrap import ensure_database_ready


def main():
    app = create_app()
    ensure_database_ready(app)
    print("TruthLens AI database initialized.")


if __name__ == "__main__":
    main()
