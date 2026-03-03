ACTIONS = {
    "hash": {
        "code": """import hashlib
import sys
content = sys.argv[1]
hash_value = hashlib.sha256(content.encode("utf-8")).hexdigest()
print(hash_value)""",
        "man": "Hashes a string and prints its SHA-256. Use single quotes or <<EOF for strings containing double quotes. Use <<EOF for multiline input."
    },
    "wronghash": {
        "code": """print("this should never run")""",
        "man": "Test action with wrong hash to verify rejection"
    },
    "notwhitelisted": {
        "code": """
print("this should never run")
""",
        "man": "Test action intentionally excluded from whitelist to verify rejection"
    }
}