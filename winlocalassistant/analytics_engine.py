"""
Analytics Engine for Nova
Provides comprehensive monitoring, performance tracking, and analytics across:
- Model performance (latency, accuracy, cost, token usage)
- Tool execution patterns and effectiveness
- Request patterns and workload analysis
- System health and resource usage
"""

import json
import logging
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Any
from collections import defaultdict

from .config import APP_DIR
from .safe_io import read_json_file, atomic_write_json, append_jsonl


ANALYTICS_DIR = Path(APP_DIR) / "analytics"
ANALYTICS_DIR.mkdir(exist_ok=True, parents=True)

MODEL_METRICS_FILE = ANALYTICS_DIR / "model_metrics.jsonl"
TOOL_METRICS_FILE = ANALYTICS_DIR / "tool_metrics.jsonl"
REQUEST_LOG_FILE = ANALYTICS_DIR / "request_log.jsonl"
LOGGER = logging.getLogger(__name__)


@dataclass
class ModelMetric:
    timestamp: str
    model: str
    provider: str  # "ollama", "openrouter", "openai", etc.
    latency_ms: float
    input_tokens: int
    output_tokens: int
    success: bool
    error: Optional[str] = None
    temperature: float = 0.7
    cost_usd: Optional[float] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ToolMetric:
    timestamp: str
    tool_name: str
    command: str
    latency_ms: float
    success: bool
    error: Optional[str] = None
    output_tokens: int = 0
    items_processed: int = 1

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RequestMetric:
    timestamp: str
    request_type: str  # "chat", "autonomous", "tool", "voice"
    duration_ms: float
    models_used: list[str]
    tools_used: list[str]
    success: bool
    user_id: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


class AnalyticsEngine:
    """Central analytics engine for performance monitoring"""

    def __init__(self):
        self.metrics_cache: dict[str, list] = defaultdict(list)
        self.session_start = datetime.now()

    def record_model_metric(
        self,
        model: str,
        provider: str,
        latency_ms: float,
        input_tokens: int = 0,
        output_tokens: int = 0,
        success: bool = True,
        error: Optional[str] = None,
        temperature: float = 0.7,
        cost_usd: Optional[float] = None,
    ) -> None:
        """Record a model execution metric"""
        metric = ModelMetric(
            timestamp=datetime.now().isoformat(),
            model=model,
            provider=provider,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            success=success,
            error=error,
            temperature=temperature,
            cost_usd=cost_usd,
        )
        try:
            append_jsonl(MODEL_METRICS_FILE, metric.to_dict())
            self.metrics_cache["models"].append(metric)
        except Exception:
            LOGGER.debug("Suppressed analytics model metric write failure", exc_info=True)

    def record_tool_metric(
        self,
        tool_name: str,
        command: str,
        latency_ms: float,
        success: bool = True,
        error: Optional[str] = None,
        output_tokens: int = 0,
        items_processed: int = 1,
    ) -> None:
        """Record a tool execution metric"""
        metric = ToolMetric(
            timestamp=datetime.now().isoformat(),
            tool_name=tool_name,
            command=command,
            latency_ms=latency_ms,
            success=success,
            error=error,
            output_tokens=output_tokens,
            items_processed=items_processed,
        )
        try:
            append_jsonl(TOOL_METRICS_FILE, metric.to_dict())
            self.metrics_cache["tools"].append(metric)
        except Exception:
            LOGGER.debug("Suppressed analytics tool metric write failure", exc_info=True)

    def record_request(
        self,
        request_type: str,
        duration_ms: float,
        models_used: list[str],
        tools_used: list[str],
        success: bool = True,
        user_id: Optional[str] = None,
    ) -> None:
        """Record a high-level request metric"""
        metric = RequestMetric(
            timestamp=datetime.now().isoformat(),
            request_type=request_type,
            duration_ms=duration_ms,
            models_used=models_used,
            tools_used=tools_used,
            success=success,
            user_id=user_id,
        )
        try:
            append_jsonl(REQUEST_LOG_FILE, metric.to_dict())
            self.metrics_cache["requests"].append(metric)
        except Exception:
            LOGGER.debug("Suppressed analytics request metric write failure", exc_info=True)

    def get_model_stats(self, hours: int = 24) -> dict[str, Any]:
        """Get aggregated model performance statistics"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        stats = {
            "by_model": defaultdict(dict),
            "by_provider": defaultdict(dict),
            "total": {
                "requests": 0,
                "successful": 0,
                "failed": 0,
                "avg_latency_ms": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cost_usd": 0,
                # Backwards-compatible aliases for existing dashboard/report callers.
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cost_usd": 0,
            },
        }

        try:
            lines = MODEL_METRICS_FILE.read_text().strip().split("\n")
            all_metrics = [json.loads(line) for line in lines if line.strip()]
            
            recent = [m for m in all_metrics if datetime.fromisoformat(m["timestamp"]) > cutoff]
            
            if not recent:
                return stats

            latencies = []
            for m in recent:
                stats["total"]["requests"] += 1
                stats["total"]["successful"] += 1 if m["success"] else 0
                stats["total"]["failed"] += 0 if m["success"] else 1
                input_tokens = int(m.get("input_tokens", 0) or 0)
                output_tokens = int(m.get("output_tokens", 0) or 0)
                cost_usd = float(m.get("cost_usd", 0) or 0)
                stats["total"]["input_tokens"] += input_tokens
                stats["total"]["output_tokens"] += output_tokens
                stats["total"]["cost_usd"] += cost_usd
                stats["total"]["total_input_tokens"] += input_tokens
                stats["total"]["total_output_tokens"] += output_tokens
                stats["total"]["total_cost_usd"] += cost_usd
                latencies.append(m["latency_ms"])

                model = m["model"]
                provider = m["provider"]

                if model not in stats["by_model"]:
                    stats["by_model"][model] = {
                        "count": 0,
                        "success_rate": 0,
                        "avg_latency_ms": 0,
                        "total_tokens": 0,
                    }
                stats["by_model"][model]["count"] += 1
                stats["by_model"][model]["total_tokens"] += m.get("output_tokens", 0)

                if provider not in stats["by_provider"]:
                    stats["by_provider"][provider] = {"count": 0, "avg_latency_ms": 0}
                stats["by_provider"][provider]["count"] += 1

            if latencies:
                stats["total"]["avg_latency_ms"] = sum(latencies) / len(latencies)
                
        except Exception:
            LOGGER.debug("Suppressed analytics model stats read failure", exc_info=True)

        return stats

    def get_tool_stats(self, hours: int = 24) -> dict[str, Any]:
        """Get aggregated tool performance statistics"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        stats = {
            "by_tool": defaultdict(dict),
            "total": {
                "invocations": 0,
                "successful": 0,
                "failed": 0,
                "avg_latency_ms": 0,
            },
        }

        try:
            lines = TOOL_METRICS_FILE.read_text().strip().split("\n")
            all_metrics = [json.loads(line) for line in lines if line.strip()]
            
            recent = [m for m in all_metrics if datetime.fromisoformat(m["timestamp"]) > cutoff]
            
            if not recent:
                return stats

            latencies = []
            for m in recent:
                stats["total"]["invocations"] += 1
                stats["total"]["successful"] += 1 if m["success"] else 0
                stats["total"]["failed"] += 0 if m["success"] else 1
                latencies.append(m["latency_ms"])

                tool = m["tool_name"]
                if tool not in stats["by_tool"]:
                    stats["by_tool"][tool] = {
                        "count": 0,
                        "success_rate": 0,
                        "avg_latency_ms": 0,
                    }
                stats["by_tool"][tool]["count"] += 1

            if latencies:
                stats["total"]["avg_latency_ms"] = sum(latencies) / len(latencies)
                
        except Exception:
            LOGGER.debug("Suppressed analytics tool stats read failure", exc_info=True)

        return stats

    def get_request_summary(self, hours: int = 24) -> dict[str, Any]:
        """Get high-level request summary"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        summary = {
            "by_type": defaultdict(int),
            "total": 0,
            "avg_duration_ms": 0,
            "success_rate": 0,
        }

        try:
            lines = REQUEST_LOG_FILE.read_text().strip().split("\n")
            all_requests = [json.loads(line) for line in lines if line.strip()]
            
            recent = [r for r in all_requests if datetime.fromisoformat(r["timestamp"]) > cutoff]
            
            if not recent:
                return summary

            durations = []
            successes = 0
            for r in recent:
                summary["total"] += 1
                summary["by_type"][r["request_type"]] += 1
                durations.append(r["duration_ms"])
                if r["success"]:
                    successes += 1

            if durations:
                summary["avg_duration_ms"] = sum(durations) / len(durations)
            if summary["total"] > 0:
                summary["success_rate"] = successes / summary["total"]

        except Exception:
            LOGGER.debug("Suppressed analytics request summary read failure", exc_info=True)

        return summary

    def export_analytics(self, output_path: Optional[Path] = None) -> dict[str, Any]:
        """Export all analytics for review"""
        if output_path is None:
            output_path = ANALYTICS_DIR / f"analytics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        export = {
            "generated_at": datetime.now().isoformat(),
            "session_start": self.session_start.isoformat(),
            "model_stats": self.get_model_stats(hours=168),  # 7 days
            "tool_stats": self.get_tool_stats(hours=168),
            "request_summary": self.get_request_summary(hours=168),
        }

        try:
            atomic_write_json(output_path, export)
        except Exception:
            LOGGER.debug("Suppressed analytics export write failure", exc_info=True)

        return export


def render_analytics_dashboard() -> str:
    """Render analytics dashboard in markdown"""
    engine = AnalyticsEngine()
    
    model_stats = engine.get_model_stats(hours=24)
    tool_stats = engine.get_tool_stats(hours=24)
    requests = engine.get_request_summary(hours=24)

    md = "# Analytics Dashboard\n\n"
    md += f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"

    # Request summary
    md += "## Request Summary (24h)\n\n"
    md += f"- **Total Requests**: {requests['total']}\n"
    md += f"- **Avg Duration**: {requests['avg_duration_ms']:.1f}ms\n"
    md += f"- **Success Rate**: {requests['success_rate']*100:.1f}%\n\n"

    if requests['by_type']:
        md += "### By Type\n"
        for req_type, count in sorted(requests['by_type'].items(), key=lambda x: -x[1]):
            md += f"- {req_type}: {count}\n"
        md += "\n"

    # Model stats
    md += "## Model Performance (24h)\n\n"
    total = model_stats['total']
    md += f"- **Total Requests**: {total['requests']}\n"
    md += f"- **Success Rate**: {(total['successful']/max(1, total['requests']))*100:.1f}%\n"
    md += f"- **Avg Latency**: {total['avg_latency_ms']:.1f}ms\n"
    input_tokens = total.get('total_input_tokens', total.get('input_tokens', 0))
    output_tokens = total.get('total_output_tokens', total.get('output_tokens', 0))
    cost_usd = total.get('cost_usd', total.get('total_cost_usd', 0)) or 0
    md += f"- **Total Tokens**: {input_tokens + output_tokens:,}\n"
    if cost_usd > 0:
        md += f"- **Total Cost**: ${cost_usd:.4f}\n"
    md += "\n"

    if model_stats['by_model']:
        md += "### By Model\n"
        for model, stats in sorted(model_stats['by_model'].items(), key=lambda x: -x[1]['count']):
            md += f"- **{model}**: {stats['count']} requests\n"
        md += "\n"

    # Tool stats
    md += "## Tool Performance (24h)\n\n"
    tool_total = tool_stats['total']
    md += f"- **Total Invocations**: {tool_total['invocations']}\n"
    md += f"- **Success Rate**: {(tool_total['successful']/max(1, tool_total['invocations']))*100:.1f}%\n"
    md += f"- **Avg Latency**: {tool_total['avg_latency_ms']:.1f}ms\n\n"

    if tool_stats['by_tool']:
        md += "### Top Tools\n"
        for tool, stats in sorted(tool_stats['by_tool'].items(), key=lambda x: -x[1]['count'])[:10]:
            md += f"- **{tool}**: {stats['count']} calls\n"

    return md


# Global analytics engine instance
_analytics_engine: Optional[AnalyticsEngine] = None


def get_analytics_engine() -> AnalyticsEngine:
    """Get or create the global analytics engine"""
    global _analytics_engine
    if _analytics_engine is None:
        _analytics_engine = AnalyticsEngine()
    return _analytics_engine
