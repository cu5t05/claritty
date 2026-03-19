import hashlib
import sys
import os

arg = sys.argv[1] if len(sys.argv) > 1 else None

if arg is None:
    print("!-Usage: do hash <string> or do hash <filepath>-!")
    sys.exit(1)

if arg.startswith("./") or arg.startswith("/") or arg.endswith(".py"):
    if not os.path.isfile(arg):
        print(f"!-File not found: {arg}-!")
        sys.exit(1)
    with open(arg, "r") as f:
        content = f.read()
else:
    content = arg

print("---output---")
print(hashlib.sha256(content.encode("utf-8")).hexdigest())