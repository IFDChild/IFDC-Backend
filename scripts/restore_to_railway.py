"""Copy the local IFDC database into the Railway Postgres service.

Usage (from the backend folder):

    venv/Scripts/python.exe scripts/restore_to_railway.py "<DATABASE_PUBLIC_URL>"

The target URL is the DATABASE_PUBLIC_URL shown in Railway's Postgres service
variables. Tables of the same name in the target are dropped and rebuilt, so run
this before the deployed dashboard is used for real content.
"""

import os
import subprocess
import sys
import tempfile
import urllib.parse

from dotenv import dotenv_values

PG_BIN = os.getenv("PG_BIN", r"C:\Program Files\PostgreSQL\16\bin")


def parts(url):
    parsed = urllib.parse.urlparse(url)
    return {
        "host": parsed.hostname or "localhost",
        "port": str(parsed.port or 5432),
        "user": parsed.username or "postgres",
        "password": urllib.parse.unquote(parsed.password or ""),
        "name": parsed.path.lstrip("/"),
    }


def run(tool, args, password):
    command = [os.path.join(PG_BIN, tool)] + args
    result = subprocess.run(command, env=dict(os.environ, PGPASSWORD=password), text=True)
    if result.returncode != 0:
        sys.exit(f"{tool} failed with exit code {result.returncode}")


def main():
    if len(sys.argv) < 2:
        sys.exit("Pass the Railway DATABASE_PUBLIC_URL as the only argument.")

    source_url = dotenv_values(".env").get("DATABASE_URL")
    if not source_url:
        sys.exit("DATABASE_URL is missing from .env - run this from the backend folder.")

    source = parts(source_url)
    target = parts(sys.argv[1])

    dump_path = os.path.join(tempfile.gettempdir(), "ifdc_db.sql")

    print(f"Dumping local database '{source['name']}' ...")
    run("pg_dump.exe", [
        "-h", source["host"], "-p", source["port"], "-U", source["user"],
        "-d", source["name"], "--no-owner", "--no-privileges",
        "--clean", "--if-exists", "-f", dump_path,
    ], source["password"])

    size_mb = os.path.getsize(dump_path) / (1024 * 1024)
    print(f"Dump written ({size_mb:.1f} MB). Restoring into Railway host {target['host']} ...")

    run("psql.exe", [
        "-h", target["host"], "-p", target["port"], "-U", target["user"],
        "-d", target["name"], "-v", "ON_ERROR_STOP=0", "-f", dump_path,
    ], target["password"])

    print("Done. Check https://<your-railway-domain>/api/news to confirm.")


if __name__ == "__main__":
    main()
