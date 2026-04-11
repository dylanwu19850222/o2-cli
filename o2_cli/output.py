"""Output formatting with TTY detection.

- TTY: Rich colored tables
- --json: compact JSON to stdout
- Pipe (no TTY): plain text columns
"""

import json
import sys
from typing import Any

from rich.console import Console
from rich.table import Table


def is_tty() -> bool:
    return sys.stdout.isatty()


class OutputFormatter:
    """Handles all output formatting with TTY detection."""

    def __init__(self, json_mode: bool = False):
        self.json_mode = json_mode
        if json_mode:
            self._console = Console(file=sys.stderr)  # JSON goes to stdout, errors to stderr
        elif is_tty():
            self._console = Console()
        else:
            self._console = Console(force_terminal=False, no_color=True)

    def print_json(self, data: Any) -> None:
        """Print data as JSON to stdout."""
        print(json.dumps(data, indent=2, default=str))

    def print_error(self, message: str, code: str | None = None) -> None:
        """Print error message."""
        if self.json_mode:
            error_data = {"error": message}
            if code:
                error_data["code"] = code
            print(json.dumps(error_data), file=sys.stderr)
        else:
            self._console.print(f"[bold red]Error:[/bold red] {message}")

    def print_success(self, message: str) -> None:
        """Print success message."""
        if not self.json_mode:
            self._console.print(f"[bold green]✓[/bold green] {message}")

    def print_balance(self, data: dict) -> None:
        """Format and print balance info."""
        if self.json_mode:
            self.print_json(data)
            return

        # Dual balance system: cash + bonus
        cash = data.get("cash", data.get("data", {}))
        bonus = data.get("bonus", {})
        summary = data.get("summary", {})

        if summary:
            self._console.print("\n[bold]Account Summary[/bold]")
            self._console.print(f"  Total:        ${summary.get('total', '0')}")
            self._console.print(f"  Withdrawable: ${summary.get('withdrawable', '0')}")
            self._console.print(f"  Trading:      ${summary.get('trading', '0')}")

        if cash:
            self._console.print("\n[bold cyan]Cash Account[/bold cyan]")
            self._console.print(f"  Available: ${cash.get('available', cash.get('available_balance', '0'))}")
            self._console.print(f"  Frozen:    ${cash.get('frozen', cash.get('frozen_balance', '0'))}")

        if bonus:
            self._console.print("\n[bold magenta]Bonus Account[/bold magenta]")
            self._console.print(f"  Available: ${bonus.get('available', '0')}")
            self._console.print(f"  Frozen:    ${bonus.get('frozen', '0')}")

        if not summary and not cash and not bonus:
            # Fallback: just print what we got
            self._console.print(data)

    def print_orders(self, data: dict) -> None:
        """Format and print orders."""
        if self.json_mode:
            self.print_json(data)
            return

        orders = data.get("orders", data if isinstance(data, list) else [])
        total = data.get("total", len(orders) if isinstance(orders, list) else 0)

        if not orders:
            self._console.print("[dim]No orders found.[/dim]")
            return

        table = Table(title=f"Orders ({total})")
        table.add_column("Order ID", style="dim", max_width=12)
        table.add_column("Market", justify="right")
        table.add_column("Side", style="bold")
        table.add_column("Type")
        table.add_column("Amount")
        table.add_column("Price")
        table.add_column("Status")
        table.add_column("Time")

        for order in orders:
            side = str(order.get("side", ""))
            side_style = "green" if side == "long" else "red" if side == "short" else ""
            status = str(order.get("status", ""))
            status_style = "yellow" if status == "open" else "green" if status == "filled" else "dim"

            table.add_row(
                str(order.get("order_id", ""))[:12],
                str(order.get("market_id", "")),
                f"[{side_style}]{side}[/{side_style}]",
                str(order.get("order_type", "")),
                str(order.get("base_amount", order.get("base_units", ""))),
                str(order.get("price", "-") or "-"),
                f"[{status_style}]{status}[/{status_style}]",
                str(order.get("created_at", ""))[:19],
            )

        self._console.print(table)

    def print_positions(self, data: dict) -> None:
        """Format and print positions."""
        if self.json_mode:
            self.print_json(data)
            return

        positions = data.get("positions", data if isinstance(data, list) else [])

        if not positions:
            self._console.print("[dim]No open positions.[/dim]")
            return

        table = Table(title="Positions")
        table.add_column("Market", justify="right")
        table.add_column("Side", style="bold")
        table.add_column("Size")
        table.add_column("Entry")
        table.add_column("Mark")
        table.add_column("PnL")
        table.add_column("Leverage")

        for pos in positions:
            side = str(pos.get("side", ""))
            side_style = "green" if side == "long" else "red"
            pnl = pos.get("unrealized_pnl", "0")
            pnl_style = "green" if str(pnl).startswith("-") is False and str(pnl) != "0" else "red"

            table.add_row(
                str(pos.get("market_id", "")),
                f"[{side_style}]{side}[/{side_style}]",
                str(pos.get("base_units", "")),
                str(pos.get("entry_price", "")),
                str(pos.get("mark_price", "-") or "-"),
                f"[{pnl_style}]{pnl}[/{pnl_style}]",
                str(pos.get("leverage", "-") or "-"),
            )

        self._console.print(table)

    def print_markets(self, data: dict) -> None:
        """Format and print markets list."""
        if self.json_mode:
            self.print_json(data)
            return

        markets = data.get("markets", data if isinstance(data, list) else [])

        if not markets:
            self._console.print("[dim]No markets found.[/dim]")
            return

        table = Table(title="Markets")
        table.add_column("ID", justify="right", style="bold")
        table.add_column("Symbol")
        table.add_column("Mark Price", justify="right")
        table.add_column("Status")

        for m in markets:
            table.add_row(
                str(m.get("market_id", m.get("marketId", m.get("id", "")))),
                str(m.get("symbol", m.get("name", m.get("base_symbol", m.get("baseToken", ""))))),
                str(m.get("mark_price", m.get("price", "-")) or "-"),
                "active" if m.get("isActive", m.get("is_active", True)) else "inactive",
            )

        self._console.print(table)

    def print_orderbook(self, data: dict) -> None:
        """Format and print order book."""
        if self.json_mode:
            self.print_json(data)
            return

        bids = data.get("bids", [])
        asks = data.get("asks", [])

        table = Table(title="Order Book")
        table.add_column("Price", justify="right", style="green")
        table.add_column("Size", justify="right")
        table.add_column("Side")

        # Show asks (reversed, highest first)
        for ask in reversed(asks[:10]):
            table.add_row(str(ask[0]), str(ask[1]), "[red]Ask[/red]")

        table.add_row("─" * 12, "─" * 10, "─" * 5)

        # Show bids
        for bid in bids[:10]:
            table.add_row(str(bid[0]), str(bid[1]), "[green]Bid[/green]")

        self._console.print(table)

    def print_raw(self, data: Any) -> None:
        """Print data with best-effort formatting."""
        if self.json_mode:
            self.print_json(data)
        elif isinstance(data, dict):
            self._console.print(data)
        else:
            self._console.print(str(data))
