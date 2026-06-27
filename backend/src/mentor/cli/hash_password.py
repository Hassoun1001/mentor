"""Generate a bcrypt hash for `MENTOR_AUTH_PASSWORD_HASH`.

Usage::

    python -m mentor.cli.hash_password

Prompts for the password (no echo) and prints the hash. Never echo the
password to the terminal, never accept it on argv (would land in shell
history).
"""

from __future__ import annotations

import getpass
import sys

from mentor.application.auth import hash_password


def main() -> None:
    try:
        pw = getpass.getpass("New password: ")
        confirm = getpass.getpass("Confirm: ")
    except (EOFError, KeyboardInterrupt):
        sys.exit(1)
    if pw != confirm:
        sys.stderr.write("passwords don't match\n")
        sys.exit(2)
    if len(pw) < 8:
        sys.stderr.write("password must be at least 8 characters\n")
        sys.exit(2)
    print(hash_password(pw))


if __name__ == "__main__":
    main()
