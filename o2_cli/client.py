"""Async httpx API client for O2 Backend.

All HTTP calls flow through this single class.
Automatically injects auth headers (JWT or API Key).
Handles O2Response envelope: {success, data, error, code, timestamp}.
"""

from typing import Any, Optional

import httpx

from o2_cli.exceptions import APIError, ConnectionError


class O2Client:
    """Async HTTP client for O2 Backend API."""

    def __init__(self, base_url: str, timeout: float = 30.0):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._token: Optional[str] = None
        self._api_key_id: Optional[str] = None
        self._api_secret: Optional[str] = None
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "O2Client":
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
            self._client = None

    def set_jwt(self, token: str) -> None:
        self._token = token

    def set_api_key(self, key_id: str, secret: str) -> None:
        self._api_key_id = key_id
        self._api_secret = secret

    def _build_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        if self._api_key_id and self._api_secret:
            headers["X-API-Key-ID"] = self._api_key_id
            headers["X-API-Secret"] = self._api_secret
        return headers

    async def _request(self, method: str, path: str, **kwargs) -> dict[str, Any]:
        """Core request method. Handles O2Response envelope."""
        if not self._client:
            raise RuntimeError("Client not initialized. Use 'async with O2Client(...)'")

        try:
            response = await self._client.request(
                method, path, headers=self._build_headers(), **kwargs
            )
        except httpx.ConnectError as e:
            raise ConnectionError(
                f"Cannot connect to {self._base_url}. Is the O2 backend running?"
            ) from e
        except httpx.TimeoutException as e:
            raise ConnectionError(
                f"Request timed out after {self._timeout}s. Try --timeout 60."
            ) from e
        except httpx.HTTPError as e:
            raise ConnectionError(f"Request failed: {e}") from e

        # Parse response
        try:
            body = response.json()
        except Exception:
            if response.status_code >= 400:
                raise APIError(response.status_code, response.text)
            return {"data": response.text}

        # Handle O2Response envelope
        if isinstance(body, dict):
            if "success" in body:
                if not body["success"]:
                    # BatchOrderResponse uses "errors" (list), standard response uses "error" (string)
                    error_msg = (
                        body.get("error")
                        or body.get("message")
                        or (body.get("errors") or [{}])[0].get("error")
                        or "Unknown error"
                    )
                    error_code = body.get("code")
                    raise APIError(response.status_code, error_msg, error_code)
                data = body.get("data")
                return data if data is not None else body
            # Some endpoints return raw dicts without envelope
            return body

        return {"data": body}

    async def get(self, path: str, params: dict | None = None) -> dict[str, Any]:
        return await self._request("GET", path, params=params)

    async def post(self, path: str, json: dict | None = None) -> dict[str, Any]:
        return await self._request("POST", path, json=json or {})

    async def put(self, path: str, json: dict | None = None) -> dict[str, Any]:
        return await self._request("PUT", path, json=json or {})

    async def delete(self, path: str) -> dict[str, Any]:
        return await self._request("DELETE", path)

    # ── Auth ──────────────────────────────────────────────

    async def auth_challenge(self, wallet_address: str) -> dict:
        return await self.post("/auth/challenge", {"wallet_address": wallet_address})

    async def auth_signature_login(
        self, wallet_address: str, signature: str, message: str
    ) -> dict:
        return await self.post(
            "/auth/signature-login",
            {
                "wallet_address": wallet_address,
                "signature": signature,
                "message": message,
            },
        )

    async def auth_test_login(self) -> dict:
        return await self.post("/auth/test-login")

    async def auth_me(self) -> dict:
        return await self.get("/auth/me")

    async def auth_session_status(self) -> dict:
        return await self.get("/auth/session-status")

    async def auth_refresh(self, token: str) -> dict:
        self._token = token
        return await self.post("/auth/refresh")

    # ── Balance ───────────────────────────────────────────

    async def get_balance(self) -> dict:
        return await self.get("/balance")

    async def get_balance_history(self, limit: int = 50, offset: int = 0) -> dict:
        return await self.get("/balance/history", {"limit": limit, "offset": offset})

    # ── Orders ────────────────────────────────────────────

    async def create_order(self, **kwargs) -> dict:
        return await self.post("/orders", kwargs)

    async def list_orders(
        self, market_id: int | None = None, status_filter: str | None = None
    ) -> dict:
        params = {}
        if market_id is not None:
            params["market_id"] = market_id
        if status_filter:
            params["status_filter"] = status_filter
        return await self.get("/orders", params or None)

    async def cancel_order(self, order_id: str) -> dict:
        return await self.post("/orders/cancel", {"order_id": order_id})

    async def cancel_all_orders(self, market_id: int | None = None) -> dict:
        payload = {}
        if market_id is not None:
            payload["market_id"] = market_id
        return await self.post("/orders/cancel-all", payload)

    async def modify_order(self, order_id: str, **kwargs) -> dict:
        kwargs["order_id"] = order_id
        return await self.post("/orders/modify", kwargs)

    async def batch_orders(self, operations: list) -> dict:
        return await self.post("/orders/batch", {"orders": operations})

    # ── Positions ─────────────────────────────────────────

    async def get_positions(self) -> dict:
        return await self.get("/positions")

    async def get_position_by_market(self, market_id: int) -> dict:
        return await self.get(f"/positions/market/{market_id}")

    async def close_position(self, position_id: str) -> dict:
        return await self.post(f"/positions/close/{position_id}")

    async def get_liquidation_risk(self, market_id: int) -> dict:
        return await self.get(f"/positions/liquidation-risk/{market_id}")

    # ── Markets ───────────────────────────────────────────

    async def get_markets(self) -> dict:
        return await self.get("/markets")

    async def get_orderbook(self, market_id: int) -> dict:
        return await self.get(f"/markets/{market_id}/orderbook")

    async def get_market_trades(self, market_id: int, limit: int = 50) -> dict:
        return await self.get(f"/markets/{market_id}/trades", {"limit": limit})

    async def get_candles(
        self, market_id: int, interval: str = "1h", limit: int = 500
    ) -> dict:
        return await self.get(
            f"/markets/{market_id}/candles", {"interval": interval, "limit": limit}
        )

    # ── Trades ────────────────────────────────────────────

    async def get_trades(
        self, skip: int = 0, limit: int = 50, market_id: int | None = None
    ) -> dict:
        params = {"skip": skip, "limit": limit}
        if market_id is not None:
            params["market_id"] = market_id
        return await self.get("/trades", params)

    async def get_trade_summary(self) -> dict:
        return await self.get("/trades/summary")

    # ── Fees ──────────────────────────────────────────────

    async def get_fee_rates(self) -> dict:
        return await self.get("/fees/rates")

    async def estimate_fee(self, base_amount: str, price: str, is_maker: bool = False) -> dict:
        return await self.post(
            "/fees/estimate",
            {"base_amount": base_amount, "price": price, "is_maker": is_maker},
        )

    # ── Deposits ──────────────────────────────────────────

    async def get_deposit_address(self, chain: str = "base") -> dict:
        return await self.get("/deposits/address", {"chain": chain})

    async def get_deposit_history(self, limit: int = 50) -> dict:
        return await self.get("/deposits/history", {"limit": limit})

    # ── Withdrawals ───────────────────────────────────────

    async def create_withdrawal(
        self, amount: str, address: str, chain: str = "ethereum", currency: str = "USDC"
    ) -> dict:
        return await self.post(
            "/withdrawals/create",
            {
                "amount": amount,
                "to_address": address,
                "chain": chain,
                "currency": currency,
            },
        )

    async def get_withdrawal(self, withdrawal_id: str) -> dict:
        return await self.get(f"/withdrawals/{withdrawal_id}")

    async def cancel_withdrawal(self, withdrawal_id: str) -> dict:
        return await self.post(f"/withdrawals/{withdrawal_id}/cancel")

    async def get_withdrawal_history(self, limit: int = 20, offset: int = 0) -> dict:
        return await self.get("/withdrawals", {"limit": limit, "offset": offset})

    # ── Settings ──────────────────────────────────────────

    async def get_user_settings(self) -> dict:
        return await self.get("/user-settings")

    async def set_leverage(self, market_id: int, leverage: int) -> dict:
        return await self.post(f"/user-settings/leverage/{market_id}", {"leverage": leverage})

    async def set_margin_mode(self, mode: str) -> dict:
        return await self.post("/user-settings/margin-mode", {"margin_mode": mode})

    async def set_hedging_mode(self, mode: str) -> dict:
        return await self.post("/user-settings/hedging-mode", {"hedging_mode": mode})

    # ── Notifications ─────────────────────────────────────

    async def get_notifications(self, **kwargs) -> dict:
        return await self.get("/notifications", kwargs or None)

    async def get_unread_count(self) -> dict:
        return await self.get("/notifications/unread-count")

    async def mark_notification_read(self, notification_id: str) -> dict:
        return await self.put(f"/notifications/{notification_id}/read")

    # ── Account ───────────────────────────────────────────

    async def get_account_overview(self) -> dict:
        return await self.get("/account/overview")

    # ── Market Maker ──────────────────────────────────────

    async def mm_status(self) -> dict:
        return await self.get("/market-maker/status")

    async def mm_start(self) -> dict:
        return await self.post("/market-maker/start")

    async def mm_stop(self) -> dict:
        return await self.post("/market-maker/stop")

    async def mm_stats(self) -> dict:
        return await self.get("/market-maker-stats/overview")

    async def mm_orders(self) -> dict:
        return await self.get("/market-maker-orders/current")
