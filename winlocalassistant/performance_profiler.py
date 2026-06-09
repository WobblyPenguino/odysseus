"""
Performance Profiler and Optimization Advisor
Analyzes system performance patterns and provides optimization recommendations.
"""

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Any
from collections import defaultdict
import json

from .config import APP_DIR
from .safe_io import append_jsonl, read_json_file

LOGGER = logging.getLogger(__name__)

PERF_DIR = Path(APP_DIR) / "performance"
PERF_DIR.mkdir(exist_ok=True, parents=True)

PROFILE_LOG = PERF_DIR / "profiles.jsonl"
RECOMMENDATIONS_FILE = PERF_DIR / "recommendations.json"


@dataclass
class PerformanceProfile:
    timestamp: str
    operation: str
    duration_ms: float
    category: str  # "model", "tool", "io", "computation", "wait"
    status: str  # "success", "timeout", "error"
    resource_usage: dict[str, float] = None  # cpu%, memory_mb, etc.

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "operation": self.operation,
            "duration_ms": self.duration_ms,
            "category": self.category,
            "status": self.status,
            "resource_usage": self.resource_usage or {},
        }


class PerformanceProfiler:
    """Profile and analyze performance metrics"""

    def __init__(self):
        self.profiles: list[PerformanceProfile] = []

    def record_operation(
        self,
        operation: str,
        duration_ms: float,
        category: str,
        status: str = "success",
        resource_usage: Optional[dict] = None,
    ) -> None:
        """Record an operation's performance"""
        profile = PerformanceProfile(
            timestamp=datetime.now().isoformat(),
            operation=operation,
            duration_ms=duration_ms,
            category=category,
            status=status,
            resource_usage=resource_usage,
        )
        self.profiles.append(profile)
        
        try:
            append_jsonl(PROFILE_LOG, profile.to_dict())
        except Exception:
            LOGGER.debug("Failed to append performance profile to %s", PROFILE_LOG, exc_info=True)

    def analyze_hotspots(self, hours: int = 24) -> dict[str, Any]:
        """Identify performance hotspots"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        categories = defaultdict(lambda: {"count": 0, "total_ms": 0, "max_ms": 0, "min_ms": float('inf')})
        operations = defaultdict(lambda: {"count": 0, "total_ms": 0, "max_ms": 0, "min_ms": float('inf')})

        try:
            if PROFILE_LOG.exists():
                for line in PROFILE_LOG.read_text().strip().split("\n"):
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        if datetime.fromisoformat(data["timestamp"]) < cutoff:
                            continue
                        
                        duration = data["duration_ms"]
                        cat = data["category"]
                        op = data["operation"]

                        categories[cat]["count"] += 1
                        categories[cat]["total_ms"] += duration
                        categories[cat]["max_ms"] = max(categories[cat]["max_ms"], duration)
                        categories[cat]["min_ms"] = min(categories[cat]["min_ms"], duration)

                        operations[op]["count"] += 1
                        operations[op]["total_ms"] += duration
                        operations[op]["max_ms"] = max(operations[op]["max_ms"], duration)
                        operations[op]["min_ms"] = min(operations[op]["min_ms"], duration)
                    except Exception:
                        continue
        except Exception:
            LOGGER.debug("Failed to read performance profile log from %s", PROFILE_LOG, exc_info=True)

        hotspots = {
            "by_category": {},
            "by_operation": {},
            "recommendations": [],
        }

        # Category analysis
        for cat, stats in sorted(categories.items(), key=lambda x: -x[1]["total_ms"]):
            avg_ms = stats["total_ms"] / max(1, stats["count"])
            hotspots["by_category"][cat] = {
                "count": stats["count"],
                "avg_ms": avg_ms,
                "max_ms": stats["max_ms"],
                "total_ms": stats["total_ms"],
            }

        # Operation analysis
        for op, stats in sorted(operations.items(), key=lambda x: -x[1]["total_ms"])[:20]:
            avg_ms = stats["total_ms"] / max(1, stats["count"])
            hotspots["by_operation"][op] = {
                "count": stats["count"],
                "avg_ms": avg_ms,
                "max_ms": stats["max_ms"],
            }

            # Generate recommendations
            if avg_ms > 5000:
                hotspots["recommendations"].append(
                    f"🔴 CRITICAL: '{op}' takes {avg_ms:.0f}ms avg - investigate for optimization"
                )
            elif avg_ms > 1000:
                hotspots["recommendations"].append(
                    f"🟡 WARNING: '{op}' takes {avg_ms:.0f}ms avg - consider caching or parallelization"
                )

        return hotspots

    def get_efficiency_score(self) -> float:
        """Calculate overall efficiency score (0-100)"""
        try:
            if PROFILE_LOG.exists():
                lines = PROFILE_LOG.read_text().strip().split("\n")
                profiles = [json.loads(line) for line in lines if line.strip()]
                
                if not profiles:
                    return 100.0

                # Score based on latency and success rate
                avg_latency = sum(p["duration_ms"] for p in profiles) / len(profiles)
                success_count = sum(1 for p in profiles if p["status"] == "success")
                success_rate = success_count / len(profiles) if profiles else 0

                # Latency penalty (target <500ms avg)
                latency_score = max(0, 100 - (avg_latency / 5))  # 5s = 0%, <500ms = 100%
                
                # Success rate bonus
                success_score = success_rate * 100

                return (latency_score + success_score) / 2
        except Exception:
            return 100.0

        return 100.0

    def generate_recommendations(self) -> list[str]:
        """Generate optimization recommendations"""
        recommendations = []
        hotspots = self.analyze_hotspots()

        # Add recommendations from hotspot analysis
        recommendations.extend(hotspots.get("recommendations", []))

        # Add general recommendations based on efficiency
        efficiency = self.get_efficiency_score()
        if efficiency < 60:
            recommendations.append("📊 Overall efficiency is LOW - review performance profiles and consider architectural changes")
        elif efficiency < 80:
            recommendations.append("📊 Overall efficiency is MODERATE - targeted optimizations could help")

        # Category-specific
        if hotspots["by_category"]:
            model_stats = hotspots["by_category"].get("model", {})
            if model_stats.get("avg_ms", 0) > 2000:
                recommendations.append("💡 Model latency is high - consider using smaller models or adding response caching")

        return recommendations


class ContextWindowOptimizer:
    """Optimize model context window usage"""

    @staticmethod
    def analyze_context_efficiency(context_size: int, used_tokens: int) -> dict[str, Any]:
        """Analyze context window efficiency"""
        efficiency = (used_tokens / context_size * 100) if context_size > 0 else 0
        
        return {
            "total_context": context_size,
            "used_tokens": used_tokens,
            "efficiency_percent": efficiency,
            "wasted_tokens": context_size - used_tokens,
            "recommendation": (
                "Excellent" if efficiency > 80
                else "Good" if efficiency > 60
                else "Moderate - consider more selective context" if efficiency > 40
                else "Low - aggressive context pruning needed"
            ),
        }

    @staticmethod
    def suggest_context_pruning(context: str, target_tokens: int) -> str:
        """Suggest pruned context to fit token limit"""
        # Simple strategy: keep first and last portions, remove middle
        lines = context.split("\n")
        estimated_tokens = len(context) // 4  # Rough estimate
        
        if estimated_tokens <= target_tokens:
            return context
        
        # Keep 30% from start, 30% from end
        keep_start = int(len(lines) * 0.3)
        keep_end = int(len(lines) * 0.3)
        
        pruned = "\n".join(lines[:keep_start]) + f"\n\n... [middle section pruned] ...\n\n" + "\n".join(lines[-keep_end:])
        return pruned


def render_performance_report() -> str:
    """Render performance analysis in markdown"""
    profiler = PerformanceProfiler()
    
    hotspots = profiler.analyze_hotspots(hours=24)
    efficiency = profiler.get_efficiency_score()
    recommendations = profiler.generate_recommendations()

    md = "# Performance Analysis Report\n\n"
    md += f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"

    # Overall efficiency
    md += "## Overall Efficiency\n\n"
    status = "🟢 Excellent" if efficiency >= 80 else "🟡 Good" if efficiency >= 60 else "🔴 Needs Improvement"
    md += f"**{status}** - {efficiency:.1f}/100\n\n"

    # Hotspots by category
    md += "## Performance by Category\n\n"
    if hotspots["by_category"]:
        for cat, stats in hotspots["by_category"].items():
            md += f"- **{cat}**: {stats['count']} calls, avg {stats['avg_ms']:.0f}ms\n"
    else:
        md += "No performance data available yet\n"
    md += "\n"

    # Top operations
    md += "## Slowest Operations (Top 10)\n\n"
    if hotspots["by_operation"]:
        for i, (op, stats) in enumerate(list(hotspots["by_operation"].items())[:10], 1):
            md += f"{i}. **{op}**: {stats['avg_ms']:.0f}ms avg ({stats['count']} calls)\n"
    md += "\n"

    # Recommendations
    if recommendations:
        md += "## Recommendations\n\n"
        for rec in recommendations:
            md += f"- {rec}\n"
    else:
        md += "## Recommendations\n\n✅ No critical performance issues detected\n"

    return md


# Global profiler instance
_performance_profiler: Optional[PerformanceProfiler] = None


def get_performance_profiler() -> PerformanceProfiler:
    """Get or create the global performance profiler"""
    global _performance_profiler
    if _performance_profiler is None:
        _performance_profiler = PerformanceProfiler()
    return _performance_profiler
