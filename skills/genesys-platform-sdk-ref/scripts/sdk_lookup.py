#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
from pathlib import Path


def err(msg: str) -> int:
    print(msg, file=sys.stderr)
    return 1


def find_sdk_root() -> Path:
    override = os.environ.get("GENESYS_PLATFORM_SDK_ROOT")
    if override:
      path = Path(override).expanduser().resolve()
      if (path / "package.json").is_file():
          return path
      raise FileNotFoundError(f"GENESYS_PLATFORM_SDK_ROOT does not point to a valid SDK root: {path}")

    npm_root = Path.home() / ".npm"
    if not npm_root.exists():
        raise FileNotFoundError("Local npm cache not found under ~/.npm")

    candidates = list(npm_root.rglob("purecloud-platform-client-v2/package.json"))
    if not candidates:
        raise FileNotFoundError("Could not find purecloud-platform-client-v2/package.json under ~/.npm")

    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0].parent


def read_lines(path: Path):
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def print_header(title: str):
    print(f"\n== {title} ==")


def print_location(path: Path, line_no: int):
    print(f"[{path}:{line_no}]")


def line_matches(lines, pattern):
    regex = re.compile(pattern)
    return [i for i, line in enumerate(lines) if regex.search(line)]


def extract_block(lines, start_idx):
    line = lines[start_idx]
    if "{" not in line:
        return [line]
    block = []
    depth = 0
    started = False
    for idx in range(start_idx, len(lines)):
        current = lines[idx]
        block.append(current)
        depth += current.count("{")
        if current.count("{") > 0:
            started = True
        depth -= current.count("}")
        if started and depth <= 0:
            break
    return block


def print_block(path: Path, lines, start_idx):
    block = extract_block(lines, start_idx)
    print_location(path, start_idx + 1)
    for line in block:
        print(line)


def search_symbol_in_file(path: Path, text: str, context: int = 2):
    lines = read_lines(path)
    hits = [i for i, line in enumerate(lines) if text in line]
    for idx in hits:
        start = max(0, idx - context)
        end = min(len(lines), idx + context + 1)
        print_location(path, idx + 1)
        for j in range(start, end):
            prefix = ">" if j == idx else " "
            print(f"{prefix} {lines[j]}")
        print()
    return len(hits)


def parse_signature_models(signature: str):
    return list(dict.fromkeys(re.findall(r"Models\.([A-Za-z0-9_]+)", signature)))


def parse_signature_options(signature: str):
    return list(dict.fromkeys(re.findall(r"([A-Za-z0-9_]+)\.([A-Za-z0-9_]+Options)", signature)))


def print_model_block(index_path: Path, index_lines, model_name: str):
    pattern = rf"^\s*export interface {re.escape(model_name)}\b|^\s*declare class {re.escape(model_name)}\b|^\s*export type {re.escape(model_name)}\b"
    hits = line_matches(index_lines, pattern)
    if not hits:
        print(f"(no local model block found for {model_name})")
        return False
    for hit in hits:
        print_block(index_path, index_lines, hit)
    return True


def print_request_details(sdk_root: Path, method_name: str):
    index_path = sdk_root / "index.d.ts"
    api_dir = sdk_root / "src" / "purecloud-platform-client-v2" / "api"
    index_lines = read_lines(index_path)

    print_header("SDK root")
    package = json.loads((sdk_root / "package.json").read_text(encoding="utf-8"))
    print(sdk_root)
    print(f"version={package.get('version')}")

    signature_pattern = rf"\b{re.escape(method_name)}\s*\("
    signature_hits = line_matches(index_lines, signature_pattern)
    if not signature_hits:
        print_header("TypeScript signatures")
        print("(no signature hits found)")
    else:
        print_header("TypeScript signatures")
        signature_lines = []
        for hit in signature_hits:
            print_location(index_path, hit + 1)
            print(index_lines[hit])
            print()
            signature_lines.append(index_lines[hit])

        option_pairs = []
        model_names = []
        for sig in signature_lines:
            option_pairs.extend(parse_signature_options(sig))
            model_names.extend(parse_signature_models(sig))
        option_pairs = list(dict.fromkeys(option_pairs))
        model_names = list(dict.fromkeys(model_names))

        print_header("Options interfaces")
        if not option_pairs:
            print("(no options interface referenced by the method signature)")
        else:
            for _api_name, opt_name in option_pairs:
                found = print_model_block(index_path, index_lines, opt_name)
                if not found:
                    print(f"(options interface not found: {opt_name})")

        print_header("Models")
        if not model_names:
            print("(no Models.* references found in the method signature)")
        else:
            for model in model_names:
                print(f"-- {model}")
                print_model_block(index_path, index_lines, model)
                print()

    print_header("Generated API implementation")
    api_files = sorted(api_dir.glob("*.js"))
    method_found = False
    method_pattern = re.compile(rf"\b{re.escape(method_name)}\s*\(")
    for path in api_files:
        lines = read_lines(path)
        hits = [i for i, line in enumerate(lines) if method_pattern.search(line)]
        for hit in hits:
            method_found = True
            print_block(path, lines, hit)
            print()
    if not method_found:
        print("(no generated API implementation hit found)")


def main():
    parser = argparse.ArgumentParser(description="Inspect the local Genesys Platform SDK for request shapes.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("root")

    p_request = sub.add_parser("request")
    p_request.add_argument("method_name")

    p_model = sub.add_parser("model")
    p_model.add_argument("model_name")

    p_symbol = sub.add_parser("symbol")
    p_symbol.add_argument("text")

    args = parser.parse_args()

    try:
        sdk_root = find_sdk_root()
    except FileNotFoundError as exc:
        return err(str(exc))

    if args.cmd == "root":
        package = json.loads((sdk_root / "package.json").read_text(encoding="utf-8"))
        print(f"SDK root: {sdk_root}")
        print(f"version: {package.get('version')}")
        print(f"readme: {sdk_root / 'README.md'}")
        print(f"types: {sdk_root / 'index.d.ts'}")
        print(f"api dir: {sdk_root / 'src' / 'purecloud-platform-client-v2' / 'api'}")
        return 0

    if args.cmd == "request":
        print_request_details(sdk_root, args.method_name)
        return 0

    if args.cmd == "model":
        index_path = sdk_root / "index.d.ts"
        index_lines = read_lines(index_path)
        print_header("SDK root")
        print(sdk_root)
        print_header(f"Model {args.model_name}")
        found = print_model_block(index_path, index_lines, args.model_name)
        return 0 if found else 1

    if args.cmd == "symbol":
        files = [
            sdk_root / "README.md",
            sdk_root / "index.d.ts",
            sdk_root / "src" / "purecloud-platform-client-v2" / "index.js",
            sdk_root / "src" / "purecloud-platform-client-v2" / "PureCloudRegionHosts.js",
        ]
        files.extend(sorted((sdk_root / "src" / "purecloud-platform-client-v2" / "api").glob("*.js")))
        print_header("SDK root")
        print(sdk_root)
        print_header(f"Symbol search: {args.text}")
        total = 0
        for path in files:
            if path.is_file():
                total += search_symbol_in_file(path, args.text, context=2)
        if total == 0:
            print("(no hits found)")
            return 1
        return 0

    return err("Unknown command")


if __name__ == "__main__":
    sys.exit(main())
