import re, sys

src, dst = sys.argv[1], sys.argv[2]
text = open(src, encoding="utf-8").read()

ids = {}
def repl(m):
    return ids.setdefault(m.group(0).lower(), f"ID-{len(ids) + 1}")

# UUIDs mit oder ohne {}, z.B. {d14cb478-62db-45a4-8f84-512653f1ccde}
text = re.sub(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", repl, text)
# Server-Adresse in Links
text = re.sub(r"https?://[^/\"]+", "https://adoit.example", text)

open(dst, "w", encoding="utf-8").write(text)
print(f"{len(ids)} IDs ersetzt -> {dst}")