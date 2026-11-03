#!/usr/bin/env python3
"""Check tracked public files and reachable branch commit identities. No values logged."""
import re
import json
import subprocess
import sys
import urllib.parse


def findings(text, approved_links=()):
    text = urllib.parse.unquote(text)
    text = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m[1], 16)), text)
    # Exact URLs only: no domain or prefix exemptions. All other rules still run.
    link_text = re.sub(r"https?://[^\s<>\"')\]]+", lambda m: "[approved-public-link]" if m[0] in approved_links else m[0], text)
    rules = {
        "credential": r"gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|sk-[A-Za-z0-9_-]{24,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        "personal-home": r"(?<![A-Za-z0-9])/(?:Users|home)/(?!xxx(?:/|$)|user(?:/|$)|example(?:/|$)|<)[A-Za-z0-9_.-]+/",
        "named-authority": r"[\u4e00-\u9fff]{2,4}(?:是|拥有)(?:唯一|最终|最高)(?:权限|授权人|决策权)",
        "private-workspace-link": r"https?://[^\s/]+\.(?:feishu\.cn|larksuite\.com)/(?:docx|wiki|base|drive)/[A-Za-z0-9/]+",
    }
    return [name for name, pattern in rules.items() if re.search(pattern, link_text if name == "private-workspace-link" else text)]


def git(*args):
    return subprocess.check_output(["git", *args])


def main():
    errors = []
    approved_links = set()
    try:
        entries = json.loads(git("show", ":docs/approved-public-links.json"))
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("url"), str) or not entry["url"].startswith("https://") or not isinstance(entry.get("reason"), str) or not entry["reason"].strip():
                raise ValueError("invalid approved public link entry")
            approved_links.add(entry["url"])
    except (subprocess.CalledProcessError, ValueError, TypeError):
        errors.append("docs/approved-public-links.json: missing or invalid approval record")
    paths = git("ls-files", "-z").decode().split("\0")
    for path in filter(None, paths):
        # Inspect the index, i.e. exactly what is about to be committed/published.
        data = git("show", ":" + path)
        if b"\0" in data:
            continue
        for rule in findings(data.decode("utf-8", errors="replace"), approved_links):
            errors.append(f"{path}: {rule}")
    # Excludes GitHub's immutable refs/pull and local rollback refs.
    identities = git("log", "HEAD", "--branches", "--format=%H%x09%ae%x09%ce").decode()
    for row in identities.splitlines():
        oid, author, committer = row.split("\t")
        if any(not (email.endswith("@users.noreply.github.com") or email == "noreply@github.com") for email in (author, committer)):
            errors.append(f"commit {oid[:12]}: non-noreply email; review before publishing")
    for error in errors:
        print(error)
    print(f"Public privacy check: {'FAIL' if errors else 'PASS'} ({len(errors)} findings)")
    return bool(errors)


if __name__ == "__main__":
    sys.exit(main())
