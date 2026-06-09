"""
Webhook System for Event-Driven Integration
Enables outbound webhooks for tool results, completions, and system events.
Supports filtering, retry logic, and event delivery tracking.
"""

import json
import logging
import threading
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Callable, Any, Literal
from enum import Enum
from collections import defaultdict

from .config import APP_DIR
from .safe_io import read_json_file, atomic_write_json, append_jsonl

LOGGER = logging.getLogger(__name__)

WEBHOOKS_DIR = Path(APP_DIR) / "webhooks"
WEBHOOKS_DIR.mkdir(exist_ok=True, parents=True)

WEBHOOKS_CONFIG = WEBHOOKS_DIR / "webhooks.json"
DELIVERY_LOG = WEBHOOKS_DIR / "deliveries.jsonl"


class EventType(Enum):
    TOOL_RESULT = "tool_result"
    TASK_COMPLETE = "task_complete"
    ERROR_OCCURRED = "error_occurred"
    MODEL_RESPONSE = "model_response"
    PROPOSAL_COMPLETE = "proposal_complete"
    SYSTEM_HEALTH = "system_health"


@dataclass
class WebhookEndpoint:
    id: str
    name: str
    url: str
    events: list[str]  # List of EventType names
    active: bool = True
    secret: Optional[str] = None  # For HMAC validation
    retry_count: int = 3
    timeout_seconds: int = 10
    headers: dict[str, str] = None
    created_at: str = None
    last_delivery: Optional[str] = None
    delivery_count: int = 0
    failed_count: int = 0

    def __post_init__(self):
        if self.headers is None:
            self.headers = {}
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        data = asdict(self)
        return data


@dataclass
class WebhookDelivery:
    webhook_id: str
    event_type: str
    payload: dict[str, Any]
    timestamp: str
    status: str  # "pending", "delivered", "failed"
    response_code: Optional[int] = None
    error_message: Optional[str] = None
    delivery_attempts: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


class WebhookManager:
    """Manages webhook endpoints and deliveries"""

    def __init__(self):
        self.endpoints: dict[str, WebhookEndpoint] = self._load_endpoints()
        self.delivery_queue: list[WebhookDelivery] = []
        self._delivery_thread: Optional[threading.Thread] = None
        self._should_stop = False

    def _load_endpoints(self) -> dict[str, WebhookEndpoint]:
        """Load webhook endpoints from config"""
        endpoints = {}
        try:
            if WEBHOOKS_CONFIG.exists():
                data = read_json_file(WEBHOOKS_CONFIG)
                for endpoint_data in data.get("endpoints", []):
                    endpoint = WebhookEndpoint(**endpoint_data)
                    endpoints[endpoint.id] = endpoint
        except Exception:
            LOGGER.debug("Failed to load webhook endpoints from %s", WEBHOOKS_CONFIG, exc_info=True)
        return endpoints

    def _save_endpoints(self) -> None:
        """Save endpoints to config"""
        try:
            data = {
                "endpoints": [ep.to_dict() for ep in self.endpoints.values()],
                "saved_at": datetime.now().isoformat(),
            }
            atomic_write_json(WEBHOOKS_CONFIG, data)
        except Exception:
            LOGGER.debug("Failed to save webhook endpoints to %s", WEBHOOKS_CONFIG, exc_info=True)

    def register_endpoint(
        self,
        name: str,
        url: str,
        events: list[str],
        secret: Optional[str] = None,
        custom_headers: Optional[dict[str, str]] = None,
    ) -> WebhookEndpoint:
        """Register a new webhook endpoint"""
        endpoint_id = f"wh_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.endpoints)}"
        
        endpoint = WebhookEndpoint(
            id=endpoint_id,
            name=name,
            url=url,
            events=events,
            secret=secret,
            headers=custom_headers or {},
        )

        self.endpoints[endpoint_id] = endpoint
        self._save_endpoints()
        return endpoint

    def unregister_endpoint(self, webhook_id: str) -> bool:
        """Unregister a webhook endpoint"""
        if webhook_id in self.endpoints:
            del self.endpoints[webhook_id]
            self._save_endpoints()
            return True
        return False

    def trigger_event(
        self,
        event_type: str,
        payload: dict[str, Any],
        async_delivery: bool = True,
    ) -> list[WebhookDelivery]:
        """Trigger an event and queue deliveries"""
        deliveries = []

        for endpoint in self.endpoints.values():
            if not endpoint.active:
                continue
            if event_type not in endpoint.events:
                continue

            delivery = WebhookDelivery(
                webhook_id=endpoint.id,
                event_type=event_type,
                payload=payload,
                timestamp=datetime.now().isoformat(),
                status="pending",
            )

            deliveries.append(delivery)
            self.delivery_queue.append(delivery)

            try:
                append_jsonl(DELIVERY_LOG, delivery.to_dict())
            except Exception:
                LOGGER.debug("Failed to append pending webhook delivery to %s", DELIVERY_LOG, exc_info=True)

        if async_delivery and deliveries:
            self._start_delivery_worker()

        return deliveries

    def _start_delivery_worker(self) -> None:
        """Start async delivery worker if not already running"""
        if self._delivery_thread is None or not self._delivery_thread.is_alive():
            self._delivery_thread = threading.Thread(
                target=self._process_deliveries,
                daemon=True,
            )
            self._delivery_thread.start()

    def _process_deliveries(self) -> None:
        """Process queued deliveries (runs in background thread)"""
        try:
            import urllib.request
            import hmac
            import hashlib
        except ImportError:
            return

        while not self._should_stop:
            if not self.delivery_queue:
                threading.Event().wait(1)  # Sleep 1 second
                continue

            delivery = self.delivery_queue.pop(0)
            endpoint = self.endpoints.get(delivery.webhook_id)
            
            if not endpoint:
                continue

            # Attempt delivery with retries
            for attempt in range(endpoint.retry_count):
                try:
                    delivery.delivery_attempts = attempt + 1
                    
                    # Prepare request
                    payload_bytes = json.dumps(delivery.payload).encode("utf-8")
                    headers = {
                        "Content-Type": "application/json",
                        "X-Webhook-Event": delivery.event_type,
                        "X-Webhook-Timestamp": delivery.timestamp,
                        **endpoint.headers,
                    }

                    # Add HMAC signature if secret is configured
                    if endpoint.secret:
                        signature = hmac.new(
                            endpoint.secret.encode(),
                            payload_bytes,
                            hashlib.sha256,
                        ).hexdigest()
                        headers["X-Webhook-Signature"] = f"sha256={signature}"

                    req = urllib.request.Request(
                        endpoint.url,
                        data=payload_bytes,
                        headers=headers,
                        method="POST",
                    )

                    try:
                        with urllib.request.urlopen(
                            req,
                            timeout=endpoint.timeout_seconds,
                        ) as response:
                            delivery.status = "delivered"
                            delivery.response_code = response.status
                            endpoint.last_delivery = datetime.now().isoformat()
                            endpoint.delivery_count += 1
                            break  # Success, exit retry loop
                    except urllib.error.HTTPError as e:
                        delivery.response_code = e.code
                        delivery.error_message = str(e)
                        if attempt == endpoint.retry_count - 1:
                            delivery.status = "failed"
                            endpoint.failed_count += 1

                except Exception as e:
                    delivery.error_message = str(e)
                    if attempt == endpoint.retry_count - 1:
                        delivery.status = "failed"
                        endpoint.failed_count += 1

            # Update delivery log
            try:
                append_jsonl(DELIVERY_LOG, delivery.to_dict())
            except Exception:
                LOGGER.debug("Failed to append webhook delivery result to %s", DELIVERY_LOG, exc_info=True)

        self._save_endpoints()

    def get_delivery_stats(self, hours: int = 24) -> dict[str, Any]:
        """Get webhook delivery statistics"""
        cutoff = datetime.now() - timedelta(hours=hours)
        stats = {
            "total": 0,
            "delivered": 0,
            "failed": 0,
            "by_webhook": defaultdict(dict),
            "by_event": defaultdict(dict),
        }

        try:
            if DELIVERY_LOG.exists():
                for line in DELIVERY_LOG.read_text().strip().split("\n"):
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        if datetime.fromisoformat(data["timestamp"]) < cutoff:
                            continue

                        stats["total"] += 1
                        if data["status"] == "delivered":
                            stats["delivered"] += 1
                        elif data["status"] == "failed":
                            stats["failed"] += 1

                        webhook_id = data["webhook_id"]
                        event_type = data["event_type"]
                        
                        if webhook_id not in stats["by_webhook"]:
                            stats["by_webhook"][webhook_id] = {"count": 0, "failed": 0}
                        stats["by_webhook"][webhook_id]["count"] += 1
                        if data["status"] == "failed":
                            stats["by_webhook"][webhook_id]["failed"] += 1

                        if event_type not in stats["by_event"]:
                            stats["by_event"][event_type] = {"count": 0, "failed": 0}
                        stats["by_event"][event_type]["count"] += 1
                        if data["status"] == "failed":
                            stats["by_event"][event_type]["failed"] += 1

                    except Exception:
                        continue
        except Exception:
            LOGGER.debug("Failed to read webhook delivery stats from %s", DELIVERY_LOG, exc_info=True)

        return stats

    def stop(self) -> None:
        """Stop the delivery worker"""
        self._should_stop = True
        if self._delivery_thread:
            self._delivery_thread.join(timeout=5)


def render_webhooks_status() -> str:
    """Render webhook status in markdown"""
    manager = WebhookManager()
    
    md = "# Webhook Status\n\n"
    md += f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"

    # Active endpoints
    active = [ep for ep in manager.endpoints.values() if ep.active]
    md += f"## Active Endpoints ({len(active)})\n\n"
    
    for endpoint in active:
        status = "✅" if endpoint.last_delivery else "⏳"
        md += f"### {status} {endpoint.name}\n"
        md += f"- **URL**: {endpoint.url}\n"
        md += f"- **Events**: {', '.join(endpoint.events)}\n"
        md += f"- **Deliveries**: {endpoint.delivery_count} successful, {endpoint.failed_count} failed\n"
        if endpoint.last_delivery:
            md += f"- **Last Delivery**: {endpoint.last_delivery}\n"
        md += "\n"

    # Stats
    stats = manager.get_delivery_stats(hours=24)
    md += "## Delivery Statistics (24h)\n\n"
    md += f"- **Total**: {stats['total']}\n"
    md += f"- **Delivered**: {stats['delivered']}\n"
    md += f"- **Failed**: {stats['failed']}\n"
    if stats['total'] > 0:
        md += f"- **Success Rate**: {(stats['delivered']/stats['total']*100):.1f}%\n"

    return md


# Global webhook manager
_webhook_manager: Optional[WebhookManager] = None


def get_webhook_manager() -> WebhookManager:
    """Get or create the global webhook manager"""
    global _webhook_manager
    if _webhook_manager is None:
        _webhook_manager = WebhookManager()
    return _webhook_manager
