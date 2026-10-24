"""Allow `python -m jarvis` to run the CLI."""

from jarvis.cli.main import main

if __name__ == "__main__":
    raise SystemExit(main())
