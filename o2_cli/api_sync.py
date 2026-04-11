"""API spec diff checker - detect backend API changes.

Compares current OpenAPI spec against a saved baseline.
Reports new, removed, and changed endpoints.

Usage:
    o2 admin api-diff              # Show changes since last snapshot
    o2 admin api-diff --snapshot   # Save current spec as new baseline
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table

from o2_cli import __version__

console = Console()

SPEC_FILE = Path.home() / ".o2" / "api-spec-baseline.json"


def fetch_openapi_spec(api_url: str, timeout: float = 10.0) -> dict:
    """Fetch OpenAPI spec from the backend."""
    import httpx

    url = api_url.rstrip("/") + "/../openapi.json"  # go up from /api/v1
    try:
        resp = httpx.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        # Fallback: try /openapi.json directly
        url2 = api_url.rstrip("/").rsplit("/api", 1)[0] + "/openapi.json"
        resp = httpx.get(url2, timeout=timeout)
        resp.raise_for_status()
        return resp.json()


def save_snapshot(spec: dict) -> None:
    """Save spec as baseline."""
    SPEC_FILE.parent.mkdir(parents=True, exist_ok=True)
    SPEC_FILE.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")


def load_snapshot() -> Optional[dict]:
    """Load saved baseline spec."""
    if not SPEC_FILE.exists():
        return None
    return json.loads(SPEC_FILE.read_text(encoding="utf-8"))


def extract_endpoints(spec: dict) -> dict[str, dict]:
    """Extract endpoint -> schema mapping from OpenAPI spec."""
    endpoints = {}
    for path, methods in spec.get("paths", {}).items():
        for method, details in methods.items():
            if method in ("get", "post", "put", "delete", "patch"):
                key = f"{method.upper()} {path}"
                # Extract parameter names and response schema hash
                params = [p.get("name", "") for p in details.get("parameters", [])]
                req_body = bool(details.get("requestBody"))
                summary = details.get("summary", "")
                endpoints[key] = {
                    "params": sorted(params),
                    "has_body": req_body,
                    "summary": summary,
                }
    return endpoints


def diff_specs(old_spec: dict, new_spec: dict) -> dict:
    """Compare two OpenAPI specs and return differences."""
    old_eps = extract_endpoints(old_spec)
    new_eps = extract_endpoints(new_spec)

    old_keys = set(old_eps.keys())
    new_keys = set(new_eps.keys())

    added = new_keys - old_keys
    removed = old_keys - new_keys
    common = old_keys & new_keys

    changed = []
    for key in sorted(common):
        if old_eps[key] != new_eps[key]:
            changed.append({
                "endpoint": key,
                "old": old_eps[key],
                "new": new_eps[key],
            })

    # Version info
    old_info = old_spec.get("info", {})
    new_info = new_spec.get("info", {})

    return {
        "old_version": old_info.get("version", "?"),
        "new_version": new_info.get("version", "?"),
        "added": sorted(added),
        "removed": sorted(removed),
        "changed": changed,
        "total_old": len(old_eps),
        "total_new": len(new_eps),
    }


def print_diff(result: dict) -> None:
    """Pretty-print the diff result."""
    has_changes = result["added"] or result["removed"] or result["changed"]

    if not has_changes:
        console.print("[green]API spec unchanged.[/green] No new, removed, or changed endpoints.")
        console.print(f"  Baseline: v{result['old_version']}, {result['total_old']} endpoints")
        return

    console.print(f"\n[bold]API Diff[/bold] (baseline v{result['old_version']} → current v{result['new_version']})")
    console.print(f"  Endpoints: {result['total_old']} → {result['total_new']}\n")

    if result["added"]:
        table = Table(title=f"New Endpoints ({len(result['added'])})", style="green")
        table.add_column("Method")
        table.add_column("Path")
        table.add_column("Summary")
        for ep in result["added"]:
            method, path = ep.split(" ", 1)
            table.add_row(method, path, "")
        console.print(table)

    if result["removed"]:
        table = Table(title=f"Removed Endpoints ({len(result['removed'])})", style="red")
        table.add_column("Method")
        table.add_column("Path")
        for ep in result["removed"]:
            method, path = ep.split(" ", 1)
            table.add_row(method, path)
        console.print(table)

    if result["changed"]:
        table = Table(title=f"Changed Endpoints ({len(result['changed'])})", style="yellow")
        table.add_column("Endpoint")
        table.add_column("Change")
        for c in result["changed"]:
            old_p = ", ".join(c["old"]["params"])
            new_p = ", ".join(c["new"]["params"])
            changes = []
            if old_p != new_p:
                changes.append(f"params: [{old_p}] → [{new_p}]")
            if c["old"]["has_body"] != c["new"]["has_body"]:
                changes.append(f"body: {c['old']['has_body']} → {c['new']['has_body']}")
            if c["old"]["summary"] != c["new"]["summary"]:
                changes.append(f"summary changed")
            table.add_row(c["endpoint"], "; ".join(changes))
        console.print(table)

    console.print(f"\nRun [bold]o2 admin api-diff --snapshot[/bold] to update baseline.")


def check_api_diff(api_url: str, snapshot: bool = False) -> None:
    """Main entry: fetch current spec, compare with baseline, optionally save."""
    console.print("Fetching OpenAPI spec...")
    current_spec = fetch_openapi_spec(api_url)

    if snapshot:
        save_snapshot(current_spec)
        eps = extract_endpoints(current_spec)
        console.print(f"[green]Snapshot saved.[/green] {len(eps)} endpoints (v{current_spec['info']['version']})")
        console.print(f"  Location: {SPEC_FILE}")
        return

    baseline = load_snapshot()
    if not baseline:
        console.print("[yellow]No baseline found.[/yellow] Saving current spec as baseline.")
        save_snapshot(current_spec)
        eps = extract_endpoints(current_spec)
        console.print(f"[green]Baseline saved.[/green] {len(eps)} endpoints")
        console.print(f"  Run again to see future changes.")
        return

    result = diff_specs(baseline, current_spec)
    print_diff(result)
