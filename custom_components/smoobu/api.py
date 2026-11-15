"""Asynchroner Client für die Smoobu-API mit HMAC-SHA256-Signatur.

Warum eigener Client statt `rest:`-Integration:
Smoobu hat die alte Authentifizierung per `Api-Key`-Header zum 31.10.2026
abgeschaltet. Jede Anfrage muss jetzt einzeln signiert werden
(Zeitstempel + Nonce + Body-Hash). Das kann die REST-Integration von HA
nicht, weil Jinja keine HMAC-Funktion kennt.

Signatur laut docs.smoobu.com:
    canonical = METHOD \n PATH \n QUERY \n TIMESTAMP \n NONCE \n BODY_SHA256_HEX \n API_KEY
    X-Signature = base64(HMAC_SHA256(secret, canonical))
QUERY: Parameter alphabetisch sortiert, Schlüssel und Werte RFC-3986-kodiert,
ohne führendes "?". Die URL wird mit exakt derselben Query gesendet,
damit Signatur und Anfrage garantiert übereinstimmen.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote

import aiohttp
from yarl import URL

from .const import API_BASE_URL

_LOGGER = logging.getLogger(__name__)

# SHA-256 des leeren Strings (GET-Anfragen ohne Body).
EMPTY_BODY_HASH = hashlib.sha256(b"").hexdigest()

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=30)
MAX_PAGES = 20  # Schutz gegen Endlosschleifen bei der Seitenabfrage
PAGE_SIZE = 100  # Maximum laut API


class SmoobuError(Exception):
    """Allgemeiner API-Fehler."""


class SmoobuAuthError(SmoobuError):
    """Schlüssel ungültig, Signatur falsch oder fehlende Berechtigung (401/403)."""


class SmoobuRateLimitError(SmoobuError):
    """Ratenlimit überschritten (429, 700 Anfragen/Minute)."""


class SmoobuConnectionError(SmoobuError):
    """Netzwerk- oder Zeitüberschreitungsfehler."""


def _rfc3986(value: str) -> str:
    """RFC-3986-Kodierung: nur A-Z a-z 0-9 - _ . ~ bleiben unverändert."""
    return quote(value, safe="-_.~")


def _format_value(value: Any) -> str:
    """Python-Werte so umwandeln, wie Smoobu sie erwartet (bool → true/false)."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def build_query(params: dict[str, Any] | None) -> str:
    """Kanonische Query: sortiert, kodiert, None-Werte entfallen."""
    if not params:
        return ""
    items = [
        (_rfc3986(str(key)), _rfc3986(_format_value(val)))
        for key, val in params.items()
        if val is not None
    ]
    items.sort()
    return "&".join(f"{key}={val}" for key, val in items)


def sign(
    secret: str,
    api_key: str,
    method: str,
    path: str,
    query: str,
    timestamp: str,
    nonce: str,
    body_hash: str,
) -> str:
    """Base64-kodierte HMAC-SHA256-Signatur über den kanonischen String."""
    canonical = "\n".join(
        [method.upper(), path, query, timestamp, nonce, body_hash, api_key]
    )
    digest = hmac.new(
        secret.encode("utf-8"), canonical.encode("utf-8"), hashlib.sha256
    ).digest()
    return base64.b64encode(digest).decode("ascii")


class SmoobuClient:
    """Dünner Client für die benötigten Smoobu-Endpunkte."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        api_key: str,
        api_secret: str,
        base_url: str = API_BASE_URL,
    ) -> None:
        self._session = session
        self._api_key = api_key.strip()
        self._api_secret = api_secret.strip()
        self._base_url = base_url.rstrip("/")

    # ------------------------------------------------------------------
    # Kern: signierte Anfrage
    # ------------------------------------------------------------------
    async def request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
    ) -> Any:
        """Signierte Anfrage senden und JSON (oder None bei 204) zurückgeben."""
        query = build_query(params)
        # Body exakt so serialisieren, wie er gehasht wird (kompakt, UTF-8).
        body_bytes = (
            json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            if body is not None
            else b""
        )
        body_hash = hashlib.sha256(body_bytes).hexdigest() if body_bytes else EMPTY_BODY_HASH
        # Zeitstempel ohne Millisekunden mit "Z" – Format wie im Doku-Beispiel.
        timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        nonce = str(uuid.uuid4())  # Darf nie wiederverwendet werden.

        headers = {
            "X-API-Key": self._api_key,
            "X-Timestamp": timestamp,
            "X-Nonce": nonce,
            "X-Signature": sign(
                self._api_secret,
                self._api_key,
                method,
                path,
                query,
                timestamp,
                nonce,
                body_hash,
            ),
            "Accept": "application/json",
            "Cache-Control": "no-cache",
        }
        if body is not None:
            headers["Content-Type"] = "application/json"

        # encoded=True: yarl darf die bereits kodierte Query nicht verändern,
        # sonst stimmt die Signatur nicht mehr.
        url = URL(f"{self._base_url}{path}{'?' + query if query else ''}", encoded=True)

        try:
            async with self._session.request(
                method,
                url,
                headers=headers,
                data=body_bytes if body is not None else None,
                timeout=REQUEST_TIMEOUT,
            ) as resp:
                text = await resp.text()
                if resp.status in (401, 403):
                    raise SmoobuAuthError(f"{resp.status}: {text[:300]}")
                if resp.status == 429:
                    raise SmoobuRateLimitError(
                        f"Ratenlimit erreicht (Retry-After: "
                        f"{resp.headers.get('X-RateLimit-Retry-After')})"
                    )
                if resp.status >= 400:
                    raise SmoobuError(f"{method} {path} → {resp.status}: {text[:300]}")
                if resp.status == 204 or not text:
                    return None
                try:
                    return json.loads(text)
                except ValueError as err:
                    raise SmoobuError(f"Ungültiges JSON von {path}: {text[:200]}") from err
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise SmoobuConnectionError(f"{method} {path}: {err}") from err

    # ------------------------------------------------------------------
    # Endpunkte
    # ------------------------------------------------------------------
    async def get_me(self) -> dict[str, Any]:
        """Benutzerprofil (id, name, email) – dient auch als Schlüsseltest."""
        return await self.request("GET", "/api/me") or {}

    async def get_apartments(self) -> list[dict[str, Any]]:
        """Liste der Wohnungen (id, name)."""
        data = await self.request("GET", "/api/apartments") or {}
        return list(data.get("apartments", []))

    async def get_apartment(self, apartment_id: int) -> dict[str, Any]:
        """Details einer Wohnung (Adresse, Zimmer, Ausstattung, Preise …)."""
        return await self.request("GET", f"/api/apartments/{apartment_id}") or {}

    async def get_reservations(self, **filters: Any) -> list[dict[str, Any]]:
        """Alle Buchungen zu den Filtern, über alle Seiten.

        Filter wie in der API, z. B. arrivalFrom, arrivalTo, departureFrom,
        departureTo, apartmentId, showCancellation, excludeBlocked,
        includePriceElements (Datumswerte als YYYY-MM-DD).
        """
        bookings: list[dict[str, Any]] = []
        page = 1
        while page <= MAX_PAGES:
            params = {**filters, "page": page, "pageSize": PAGE_SIZE}
            data = await self.request("GET", "/api/reservations", params=params) or {}
            bookings.extend(data.get("bookings", []))
            page_count = int(data.get("page_count") or 1)
            if page >= page_count:
                break
            page += 1
        return bookings

    async def get_reservation(self, reservation_id: int) -> dict[str, Any]:
        """Einzelbuchung inkl. firstname/lastname, Kurtaxe, Preisdetails."""
        return await self.request("GET", f"/api/reservations/{reservation_id}") or {}

    async def get_messages(
        self, reservation_id: int, only_related_to_guest: bool = True
    ) -> list[dict[str, Any]]:
        """Nachrichten einer Buchung (alle Seiten)."""
        messages: list[dict[str, Any]] = []
        page = 1
        while page <= MAX_PAGES:
            data = (
                await self.request(
                    "GET",
                    f"/api/reservations/{reservation_id}/messages",
                    params={"page": page, "onlyRelatedToGuest": only_related_to_guest},
                )
                or {}
            )
            messages.extend(data.get("messages", []))
            if page >= int(data.get("page_count") or 1):
                break
            page += 1
        return messages

    async def send_message(
        self,
        reservation_id: int,
        message: str,
        subject: str | None = None,
        to_host: bool = False,
        internal: bool = False,
    ) -> None:
        """Nachricht an Gast (Standard) oder als Host-Notiz senden."""
        body: dict[str, Any] = {"messageBody": message}
        if subject:
            body["subject"] = subject
        if to_host:
            body["internal"] = internal
            path = f"/api/reservations/{reservation_id}/messages/send-message-to-host"
        else:
            path = f"/api/reservations/{reservation_id}/messages/send-message-to-guest"
        await self.request("POST", path, body=body)

    async def get_rates(
        self, apartment_id: int, start_date: str, end_date: str
    ) -> dict[str, dict[str, Any]]:
        """Tagespreise/Mindestaufenthalt/Verfügbarkeit einer Wohnung.

        Antwort von Smoobu: {"data": {"<aptId>": {"YYYY-MM-DD": {price,
        min_length_of_stay, available}}}} → hier nur das innere Dict.
        """
        data = (
            await self.request(
                "GET",
                "/api/rates",
                params={
                    "apartments[]": apartment_id,
                    "start_date": start_date,
                    "end_date": end_date,
                },
            )
            or {}
        )
        return (data.get("data") or {}).get(str(apartment_id)) or {}

    # --- Webhook-Verwaltung ---------------------------------------------
    async def list_webhooks(self) -> list[dict[str, Any]]:
        data = await self.request("GET", "/api/users/webhooks") or {}
        return list(data.get("webhooks", []))

    async def create_webhook(self, url: str) -> dict[str, Any]:
        return await self.request("POST", "/api/users/webhooks", body={"webhookUrl": url}) or {}

    async def delete_webhook(self, webhook_id: int | str) -> None:
        await self.request("DELETE", f"/api/users/webhooks/{webhook_id}")
