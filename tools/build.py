#!/usr/bin/env python3
"""Turns announcements/*.md into _site/announcements.json for the boards.

Each file starts with a header between --- lines (title, date, and optional
min_version, max_version, platforms, expires, draft, title_fr, title_cs).
A translation of the body goes beside it as <id>.fr.md or <id>.cs.md.
The file name (without .md) is the announcement's id: never rename one.
"""
import json, os, re, shutil, sys

src, out = sys.argv[1], sys.argv[2]
KEYS = {"title", "date", "min_version", "max_version", "platforms", "expires", "draft"}
LANGS = {"fr", "cs"}
errors, items = [], []

def split(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"---\n(.*?)\n---\n?(.*)", text, re.S)
    if not m:
        return {}, text.strip()
    head = {}
    for line in m.group(1).splitlines():
        if line.strip() and not line.lstrip().startswith("#"):
            k, _, v = line.partition(":")
            head[k.strip()] = v.strip().strip('"')
    return head, m.group(2).strip()

for name in sorted(os.listdir(src)):
    if not name.endswith(".md") or re.search(r"\.(\w\w)\.md$", name):
        continue
    ident, path = name[:-3], os.path.join(src, name)
    head, body = split(path)
    for k in head:
        if k not in KEYS and not re.fullmatch(r"title_(\w\w)", k):
            errors.append(f"{name}: unknown field '{k}'")
    if not head.get("title") or not re.fullmatch(r"\d{4}-\d\d-\d\d", head.get("date", "")):
        errors.append(f"{name}: needs a title and a date (YYYY-MM-DD)")
        continue
    item = {"id": ident, "title": head["title"], "date": head["date"], "body": body}
    for k in ("min_version", "max_version", "expires"):
        if head.get(k):
            item[k] = head[k]
    if head.get("platforms"):
        item["platforms"] = [p.strip() for p in head["platforms"].split(",") if p.strip()]
    if head.get("draft", "").lower() == "true":
        item["draft"] = True
    for lang in LANGS:
        tr = {}
        if head.get("title_" + lang):
            tr["title"] = head["title_" + lang]
        tp = os.path.join(src, f"{ident}.{lang}.md")
        if os.path.exists(tp):
            tr["body"] = split(tp)[1]
        if tr:
            item.setdefault("translations", {})[lang] = tr
    items.append(item)

if errors:
    sys.exit("\n".join(errors))
items.sort(key=lambda i: (i["date"], i["id"]), reverse=True)
os.makedirs(out, exist_ok=True)
with open(os.path.join(out, "announcements.json"), "w", encoding="utf-8") as f:
    json.dump({"version": 1, "announcements": items}, f, ensure_ascii=False, indent=1)
if os.path.isdir("images"):
    shutil.copytree("images", os.path.join(out, "images"), dirs_exist_ok=True)
print(f"{len(items)} announcements")
