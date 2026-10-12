"""
TrustLens AI — MongoDB Diagnostic & Connectivity Verification Script
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

backend_dir = Path(__file__).resolve().parent
load_dotenv(backend_dir / ".env")
load_dotenv(backend_dir.parent / ".env")

import database

print("=" * 60)
print("TrustLens AI — MongoDB Connection Diagnostic")
print("=" * 60)

raw_uri = os.getenv("MONGO_URI", "")
if not raw_uri.strip():
    print("[!] MONGO_URI is currently EMPTY in backend/.env")
    print("    Open backend/.env and set your MongoDB Atlas connection string:")
    print("    MONGO_URI=mongodb+srv://<username>:<password>@tejas.ibsgryv.mongodb.net/trustlens?retryWrites=true&w=majority")
    print("=" * 60)
    sys.exit(0)

# Mask password for safety in terminal output
masked_uri = raw_uri
if "@" in raw_uri and "://" in raw_uri:
    prefix, rest = raw_uri.split("://", 1)
    creds, host_part = rest.split("@", 1)
    masked_uri = f"{prefix}://***:***@{host_part}"

print(f"Target URI : {masked_uri}")
print(f"Target DB  : {database.DB_NAME}")
print("\nTesting connection ping...")

if not database.ping_db():
    print("[-] Could not connect to MongoDB server.")
    print("    Check your username/password and make sure your IP is allowed in MongoDB Atlas Network Access.")
    print("=" * 60)
    sys.exit(1)

print("[+] SUCCESS: Connected to MongoDB!")
col_users = database.get_users_collection()
col_logs = database.get_login_logs_collection()
col_scans = database.get_collection()

users_count = col_users.count_documents({})
logs_count = col_logs.count_documents({})
scans_count = col_scans.count_documents({})

print(f" * Collection 'users'      : {users_count} documents")
print(f" * Collection 'login_logs' : {logs_count} documents")
print(f" * Collection 'scan_logs'  : {scans_count} documents")

if users_count > 0:
    print("\nUsers found:")
    for u in col_users.find().limit(5):
        print(f"   - Email: {u.get('email')} | Name: {u.get('name')} | Status: {u.get('status')}")

print("=" * 60)
