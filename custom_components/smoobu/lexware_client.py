"""Lexware Office Public API – Client (BETA, ab v1.20.0).

- Basis `https://api.lexware.io`, Bearer-Token (API-Key aus app.lexware.de/addons/public-api; nur ab Tarif XL)
- Rate-Limit laut Doku: 2 Anfragen/s über alle Endpunkte, darüber HTTP 429 → Token-Bucket hier im Client,
  429/5xx werden mit wachsender Wartezeit bis zu 3× wiederholt
- Rechnungen entstehen immer als **Entwurf** (ohne `finalize=true`) – geprüft und finalisiert wird in Lexware
- `MockLexware` hat dieselbe Schnittstelle mit Beispieldaten: Tests, Demo-Screenshots und Ausprobieren ohne
  XL-Tarif (Option „Testmodus“). Er schreibt nie nach außen.

Was laut Doku noch live zu bestätigen ist (Testkonto), steht im Konzept unter „Offen“: Artikel-ID in
Rechnungspositionen, Feld für den Gesamtrabatt, Ansprechpartner in der Rechnungsadresse.
"""

from __future__ import annotations

import asyncio
import copy
import logging
import time
import uuid
from datetime import date, datetime
from typing import Any
from urllib.parse import quote

_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://api.lexware.io"
APP_URL = "https://app.lexware.de"
RATE = 2.0          # Anfragen je Sekunde (Lexware-Grenze)
RETRIES = 3
TIMEOUT = 20


class LexwareError(Exception):
    """Fehler der Lexware-API (status = HTTP-Status, 0 = Verbindung)."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(f"{status}: {message}")
        self.status = status
        self.message = message


class TokenBucket:
    """Einfacher Token-Bucket: höchstens `rate` Anfragen je Sekunde, gemeinsam für alle Aufrufe des Kontos."""

    def __init__(self, rate: float = RATE, monotonic: Any = time.monotonic, sleep: Any = asyncio.sleep) -> None:
        self.rate, self.tokens, self._mono, self._sleep = rate, rate, monotonic, sleep
        self.last = monotonic()
        self._lock = asyncio.Lock()

    async def take(self) -> None:
        async with self._lock:
            while True:
                now = self._mono()
                self.tokens = min(self.rate, self.tokens + (now - self.last) * self.rate)
                self.last = now
                if self.tokens >= 1:
                    self.tokens -= 1
                    return
                await self._sleep((1 - self.tokens) / self.rate)


def deeplink(kind: str, voucher_id: str, mode: str = "view") -> str:
    """Link „In Lexware öffnen“ (Doku: {appbaseurl}/permalink/<resource>/<view|edit>/<id>)."""
    return f"{APP_URL}/permalink/{kind}/{mode}/{voucher_id}"


class LexwareClient:
    """Asynchroner Client über die aiohttp-Session von Home Assistant."""

    mock = False

    def __init__(self, session: Any, api_key: str, base_url: str = BASE_URL, bucket: TokenBucket | None = None) -> None:
        self._session = session
        self._key = api_key
        self._base = base_url.rstrip("/")
        self._bucket = bucket or TokenBucket()

    async def _req(self, method: str, path: str, *, params: dict[str, Any] | None = None, json: Any = None) -> Any:
        import aiohttp  # noqa: PLC0415

        url = f"{self._base}{path}"
        headers = {"Authorization": f"Bearer {self._key}", "Accept": "application/json"}
        delay = 1.0
        for attempt in range(RETRIES + 1):
            await self._bucket.take()
            try:
                async with self._session.request(method, url, params=params, json=json, headers=headers,
                                                 timeout=aiohttp.ClientTimeout(total=TIMEOUT)) as resp:
                    if resp.status in (429, 500, 502, 503, 504) and attempt < RETRIES:
                        retry = resp.headers.get("Retry-After")
                        await asyncio.sleep(float(retry) if retry and retry.isdigit() else delay)
                        delay *= 2
                        continue
                    if resp.status == 204:
                        return None
                    text = await resp.text()
                    if resp.status >= 400:
                        raise LexwareError(resp.status, _err_text(text))
                    return await resp.json(content_type=None) if text else None
            except (aiohttp.ClientError, asyncio.TimeoutError) as err:
                if attempt < RETRIES:
                    await asyncio.sleep(delay)
                    delay *= 2
                    continue
                raise LexwareError(0, str(err) or type(err).__name__) from err
        raise LexwareError(429, "Zu viele Anfragen")

    # --- Konto -----------------------------------------------------------
    async def profile(self) -> dict[str, Any]:
        return await self._req("GET", "/v1/profile")

    # --- Artikel ---------------------------------------------------------
    async def articles(self) -> list[dict[str, Any]]:
        out, page = [], 0
        while True:
            res = await self._req("GET", "/v1/articles", params={"page": page, "size": 250})
            out += (res or {}).get("content") or []
            if (res or {}).get("last", True) or page > 20:
                return out
            page += 1

    # --- Kontakte --------------------------------------------------------
    async def contacts(self, *, name: str | None = None, email: str | None = None) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"customer": "true", "size": 100}
        if name:
            params["name"] = name
        if email:
            params["email"] = email
        res = await self._req("GET", "/v1/contacts", params=params)
        return (res or {}).get("content") or []

    async def contact(self, contact_id: str) -> dict[str, Any]:
        return await self._req("GET", f"/v1/contacts/{quote(contact_id)}")

    async def create_contact(self, data: dict[str, Any]) -> dict[str, Any]:
        return await self._req("POST", "/v1/contacts", json=data)

    async def update_contact(self, contact_id: str, data: dict[str, Any]) -> dict[str, Any]:
        return await self._req("PUT", f"/v1/contacts/{quote(contact_id)}", json=data)

    # --- Rechnungen ------------------------------------------------------
    async def create_invoice_draft(self, data: dict[str, Any]) -> dict[str, Any]:
        """Immer Entwurf (kein `finalize=true`) – Entscheidung Betreiber: geprüft wird in Lexware."""
        return await self._req("POST", "/v1/invoices", json=data)

    async def invoice(self, invoice_id: str) -> dict[str, Any]:
        return await self._req("GET", f"/v1/invoices/{quote(invoice_id)}")

    async def payments(self, voucher_id: str) -> dict[str, Any] | None:
        """Zahlungsstand; Entwürfe haben laut Doku keine Zahlungsinformation (Fehler → None)."""
        try:
            return await self._req("GET", f"/v1/payments/{quote(voucher_id)}")
        except LexwareError as err:
            if err.status in (404, 406, 409):
                return None
            raise

    # --- Webhooks (Event-Subscriptions) ----------------------------------
    async def subscriptions(self) -> list[dict[str, Any]]:
        res = await self._req("GET", "/v1/event-subscriptions")
        return (res or {}).get("content") or []

    async def subscribe(self, event_type: str, callback_url: str) -> dict[str, Any]:
        return await self._req("POST", "/v1/event-subscriptions", json={"eventType": event_type, "callbackUrl": callback_url})

    async def unsubscribe(self, subscription_id: str) -> None:
        await self._req("DELETE", f"/v1/event-subscriptions/{quote(subscription_id)}")


def _err_text(text: str) -> str:
    import json  # noqa: PLC0415

    try:
        data = json.loads(text)
    except ValueError:
        return text[:300]
    if isinstance(data, dict):
        details = data.get("details") or data.get("IssueList") or []
        msg = data.get("message") or data.get("error") or ""
        if details:
            msg += " – " + "; ".join(str(d.get("violation") or d.get("message") or d) for d in details[:5] if d)
        return msg[:300] or text[:300]
    return text[:300]


# ---------------------------------------------------------------------------
# Testmodus
# ---------------------------------------------------------------------------
DEMO_ARTICLES: list[dict[str, Any]] = [
    {"id": "demo-uebernachtung", "title": "Übernachtung 1 Person o. Verpflegung", "description": "Nachtpreis für eine Person ohne Verpflegung",
     "type": "SERVICE", "unitName": "Nächte", "price": {"leadingPrice": "GROSS", "grossPrice": 62.0, "netPrice": 57.94, "taxRate": 7}},
    {"id": "demo-person", "title": "Aufpreis 2. Person o. Verpflegung", "description": "Aufpreis je Nacht ab der 2. Person",
     "type": "SERVICE", "unitName": "Nächte", "price": {"leadingPrice": "GROSS", "grossPrice": 10.0, "netPrice": 9.35, "taxRate": 7}},
    {"id": "demo-kind", "title": "Aufpreis Kind o. Verpflegung", "type": "SERVICE", "unitName": "Nächte",
     "price": {"leadingPrice": "GROSS", "grossPrice": 5.0, "netPrice": 4.67, "taxRate": 7}},
    {"id": "demo-hund", "title": "Sonderreinigung 1 Hund", "description": "Je Hund (max. 2), erhöhtes Reinigungsaufkommen",
     "type": "SERVICE", "unitName": "Pauschal", "price": {"leadingPrice": "GROSS", "grossPrice": 10.0, "netPrice": 9.35, "taxRate": 7}},
    {"id": "demo-kurz", "title": "Endreinigung Kurzzeit", "description": "Endreinigung ≤ 14 Nächte", "type": "SERVICE",
     "unitName": "Pauschal", "price": {"leadingPrice": "GROSS", "grossPrice": 10.0, "netPrice": 9.35, "taxRate": 7}},
    {"id": "demo-lang", "title": "Endreinigung Langzeit", "description": "Endreinigung > 14 Nächte", "type": "SERVICE",
     "unitName": "Pauschal", "price": {"leadingPrice": "GROSS", "grossPrice": 30.0, "netPrice": 28.04, "taxRate": 7}},
    {"id": "demo-portal", "title": "Übernachtung [n] Person(en) o. Verpflegung", "description": "Ferienwohnung\nGebucht und bezahlt über [Portal]",
     "type": "SERVICE", "unitName": "Pauschal", "price": {"leadingPrice": "NET", "netPrice": 1.0, "grossPrice": 1.07, "taxRate": 7}},
]


class MockLexware:
    """Beispiel-Lexware im Speicher (Testmodus/Tests). Kein Netzverkehr."""

    mock = True

    def __init__(self) -> None:
        self.articles_data = copy.deepcopy(DEMO_ARTICLES)
        self.contacts_data: dict[str, dict[str, Any]] = {}
        self.invoices_data: dict[str, dict[str, Any]] = {}
        self.payments_data: dict[str, list[dict[str, Any]]] = {}
        self.subs: dict[str, dict[str, Any]] = {}
        self._no = 0

    async def profile(self) -> dict[str, Any]:
        return {"organizationId": "demo", "companyName": "Demo-Ferienwohnung", "testmodus": True}

    async def articles(self) -> list[dict[str, Any]]:
        return copy.deepcopy(self.articles_data)

    async def contacts(self, *, name: str | None = None, email: str | None = None) -> list[dict[str, Any]]:
        def hit(c: dict[str, Any]) -> bool:
            names = [str((c.get("company") or {}).get("name") or ""),
                     " ".join(filter(None, [(c.get("person") or {}).get("firstName"), (c.get("person") or {}).get("lastName")]))]
            mails = [m for v in (c.get("emailAddresses") or {}).values() for m in v]
            return (not name or any(name.lower() in n.lower() for n in names)) and (not email or email.lower() in [m.lower() for m in mails])
        return [copy.deepcopy(c) for c in self.contacts_data.values() if hit(c)]

    async def contact(self, contact_id: str) -> dict[str, Any]:
        return copy.deepcopy(self.contacts_data[contact_id])

    async def create_contact(self, data: dict[str, Any]) -> dict[str, Any]:
        cid = str(uuid.uuid4())
        self.contacts_data[cid] = {**copy.deepcopy(data), "id": cid, "version": 1,
                                   "roles": {"customer": {"number": 10000 + len(self.contacts_data) + 1}}}
        return {"id": cid, "version": 1}

    async def update_contact(self, contact_id: str, data: dict[str, Any]) -> dict[str, Any]:
        cur = self.contacts_data[contact_id]
        if data.get("version") != cur["version"]:
            raise LexwareError(409, "version conflict")
        self.contacts_data[contact_id] = {**cur, **copy.deepcopy(data), "version": cur["version"] + 1}
        return {"id": contact_id, "version": cur["version"] + 1}

    async def create_invoice_draft(self, data: dict[str, Any]) -> dict[str, Any]:
        iid = str(uuid.uuid4())
        self.invoices_data[iid] = {**copy.deepcopy(data), "id": iid, "voucherStatus": "draft", "voucherNumber": None,
                                   "createdDate": datetime.now().isoformat()}
        return {"id": iid, "version": 0}

    async def invoice(self, invoice_id: str) -> dict[str, Any]:
        if invoice_id not in self.invoices_data:
            raise LexwareError(404, "not found")
        return copy.deepcopy(self.invoices_data[invoice_id])

    async def payments(self, voucher_id: str) -> dict[str, Any] | None:
        inv = self.invoices_data.get(voucher_id)
        if not inv or inv["voucherStatus"] == "draft":
            return None
        total = float(inv.get("_total") or 0)
        paid = sum(p["amount"] for p in self.payments_data.get(voucher_id, []))
        open_amount = round(max(total - paid, 0), 2)
        status = "voided" if inv["voucherStatus"] == "voided" else ("paid" if open_amount == 0 else "open")
        return {"openAmount": 0 if status == "voided" else open_amount, "currency": "EUR",
                "paymentStatus": "balanced" if status in ("paid", "voided") else "openRevenue",
                "voucherType": "invoice", "voucherStatus": status,
                "paidDate": (self.payments_data.get(voucher_id) or [{}])[-1].get("postingDate") if status == "paid" else None,
                "paymentItems": copy.deepcopy(self.payments_data.get(voucher_id, []))}

    # Testhelfer: in Lexware finalisieren und Zahlung zuordnen (was der Betreiber in Lexware tut)
    def finalize(self, invoice_id: str, total: float) -> None:
        self._no += 1
        self.invoices_data[invoice_id].update({"voucherStatus": "open", "voucherNumber": f"RE-DEMO-{self._no:03d}", "_total": total})

    def pay(self, invoice_id: str, amount: float, day: date | None = None) -> None:
        self.payments_data.setdefault(invoice_id, []).append(
            {"paymentItemType": "partPaymentFinancialTransaction", "amount": amount, "currency": "EUR",
             "postingDate": f"{(day or date.today()).isoformat()}T00:00:00.000+01:00"})

    async def subscriptions(self) -> list[dict[str, Any]]:
        return list(self.subs.values())

    async def subscribe(self, event_type: str, callback_url: str) -> dict[str, Any]:
        sid = str(uuid.uuid4())
        self.subs[sid] = {"subscriptionId": sid, "eventType": event_type, "callbackUrl": callback_url}
        return {"id": sid}

    async def unsubscribe(self, subscription_id: str) -> None:
        self.subs.pop(subscription_id, None)
