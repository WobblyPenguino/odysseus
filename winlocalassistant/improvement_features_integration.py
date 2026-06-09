"""
Integration of new Nova improvement features as CLI commands
This module provides command adapters for the new analytics, performance, and scheduling features.
It can be loaded separately without modifying core tools.py
"""

from winlocalassistant.analytics_engine import render_analytics_dashboard, get_analytics_engine
from winlocalassistant.performance_profiler import render_performance_report, get_performance_profiler
from winlocalassistant.proposal_ledger import render_proposal_ledger, get_proposal_ledger
from winlocalassistant.webhook_system import render_webhooks_status, get_webhook_manager
from winlocalassistant.task_scheduler import render_scheduler_status, get_task_scheduler
from winlocalassistant.tools import ToolResult


def analytics_dashboard_tool(self) -> ToolResult:
    """View analytics dashboard with model, tool, and request performance metrics"""
    try:
        engine = get_analytics_engine()
        markdown = render_analytics_dashboard()
        stats = {
            "model_stats": engine.get_model_stats(hours=24),
            "tool_stats": engine.get_tool_stats(hours=24),
            "request_summary": engine.get_request_summary(hours=24),
        }
        return ToolResult(True, "Analytics dashboard generated", {"message": markdown, **stats})
    except Exception as e:
        return ToolResult(False, f"Analytics error: {str(e)}", {})


def performance_report_tool(self) -> ToolResult:
    """Generate performance analysis and optimization recommendations"""
    try:
        profiler = get_performance_profiler()
        markdown = render_performance_report()
        recommendations = profiler.generate_recommendations()
        hotspots = profiler.analyze_hotspots(hours=24)
        efficiency = profiler.get_efficiency_score()
        return ToolResult(
            True,
            f"Performance report generated (efficiency: {efficiency:.1f}/100)",
            {
                "message": markdown,
                "efficiency_score": efficiency,
                "recommendations": recommendations,
                "hotspots": hotspots,
            },
        )
    except Exception as e:
        return ToolResult(False, f"Performance analysis error: {str(e)}", {})


def webhook_management_tool(self, action: str = "status", url: str = "", events: str = "", name: str = "") -> ToolResult:
    """Manage webhook endpoints for event-driven integration"""
    try:
        manager = get_webhook_manager()
        action = (action or "status").strip().lower()
        
        if action in {"list", "status"}:
            markdown = render_webhooks_status()
            endpoints = [ep.to_dict() for ep in manager.endpoints.values()]
            return ToolResult(True, "Webhook status generated", {"message": markdown, "endpoints": endpoints})
        
        elif action in {"register", "add", "create"}:
            if not url or not events or not name:
                return ToolResult(False, "Missing required fields: name, url, events", {})
            event_list = [e.strip() for e in events.split(",")]
            endpoint = manager.register_endpoint(name, url, event_list)
            return ToolResult(True, f"Webhook registered: {name}", {"endpoint": endpoint.to_dict()})
        
        elif action in {"test"}:
            from datetime import datetime
            payload = {"test": True, "timestamp": datetime.now().isoformat()}
            deliveries = manager.trigger_event("test", payload, async_delivery=False)
            return ToolResult(True, f"Test events triggered ({len(deliveries)} endpoints)", {"deliveries": len(deliveries)})
        
        else:
            return ToolResult(False, f"Unknown webhook action: {action}", {})
    except Exception as e:
        return ToolResult(False, f"Webhook error: {str(e)}", {})


def task_scheduler_tool(self, action: str = "list", name: str = "", schedule: str = "", command: str = "", task_id: str = "") -> ToolResult:
    """Manage scheduled tasks and cron-like execution"""
    try:
        scheduler = get_task_scheduler()
        action = (action or "list").strip().lower()
        
        if action in {"list", "status"}:
            markdown = render_scheduler_status()
            tasks = [task.to_dict() for task in scheduler.tasks.values()]
            return ToolResult(True, "Scheduler status generated", {"message": markdown, "tasks": tasks})
        
        elif action in {"add", "create"}:
            if not name or not schedule or not command:
                return ToolResult(False, "Missing required: name, schedule (cron), command", {})
            task = scheduler.add_task(name, schedule, command)
            scheduler.start()
            return ToolResult(True, f"Task scheduled: {name}", {"task": task.to_dict()})
        
        elif action in {"run", "execute"}:
            if not task_id:
                return ToolResult(False, "Missing task_id", {})
            success = scheduler.execute_task(task_id)
            return ToolResult(success, f"Task execution {'succeeded' if success else 'failed'}", {})
        
        elif action in {"enable"}:
            if not task_id:
                return ToolResult(False, "Missing task_id", {})
            scheduler.enable_task(task_id)
            return ToolResult(True, "Task enabled", {})
        
        elif action in {"disable"}:
            if not task_id:
                return ToolResult(False, "Missing task_id", {})
            scheduler.disable_task(task_id)
            return ToolResult(True, "Task disabled", {})
        
        else:
            return ToolResult(False, f"Unknown scheduler action: {action}", {})
    except Exception as e:
        return ToolResult(False, f"Scheduler error: {str(e)}", {})


def proposal_ledger_tool(self) -> ToolResult:
    """View proposal ledger and track improvement completion"""
    try:
        ledger = get_proposal_ledger()
        markdown = render_proposal_ledger()
        matrix = ledger.build_impact_matrix()
        return ToolResult(True, "Proposal ledger generated", {"message": markdown, "impact_matrix": matrix})
    except Exception as e:
        return ToolResult(False, f"Ledger error: {str(e)}", {})


def completed_improvements_tool(self) -> ToolResult:
    """Show completed improvements and their validation status"""
    try:
        ledger = get_proposal_ledger()
        completed = ledger.get_completed_proposals()
        md = "# Completed Improvements\n\n"
        md += f"**Total**: {len(completed)}\n\n"
        for prop in completed[-20:]:  # Last 20
            md += f"## {prop.title}\n"
            md += f"- **Value**: {prop.value_score}/100\n"
            md += f"- **Risk**: {prop.risk_level}\n"
            md += f"- **Validated**: {prop.is_safe()}\n"
            if prop.completed_at:
                md += f"- **Completed**: {prop.completed_at}\n"
            md += "\n"
        return ToolResult(True, f"Completed improvements: {len(completed)}", {"message": md, "count": len(completed)})
    except Exception as e:
        return ToolResult(False, f"Error: {str(e)}", {})


def anti_repeat_tool(self, title: str = "", subsystems: str = "") -> ToolResult:
    """Check if similar improvements have been completed (prevent repetition)"""
    try:
        if not title:
            return ToolResult(False, "Missing proposal title", {})
        
        ledger = get_proposal_ledger()
        subsys_list = [s.strip() for s in (subsystems or "").split(",") if s.strip()]
        similar = ledger.find_similar_completed(title, subsys_list)
        
        if similar:
            md = f"⚠️ Similar completed improvements found:\n\n"
            for prop in similar:
                md += f"- **{prop.title}** (completed {prop.completed_at})\n"
            return ToolResult(True, f"Found {len(similar)} similar completed proposals", {"message": md, "similar_count": len(similar)})
        else:
            return ToolResult(True, "No similar completed improvements found - safe to proceed", {"similar_count": 0})
    except Exception as e:
        return ToolResult(False, f"Anti-repeat check error: {str(e)}", {})


def register_improvement_features(registry) -> None:
    """Register all improvement feature tools with the given ToolRegistry instance"""
    registry.register("analytics", lambda: analytics_dashboard_tool(registry))
    registry.register("analytics_dashboard", lambda: analytics_dashboard_tool(registry))
    registry.register("performance_analytics", lambda: analytics_dashboard_tool(registry))
    registry.register("performance_profiler", lambda: performance_report_tool(registry))
    registry.register("performance_report", lambda: performance_report_tool(registry))
    registry.register("optimize_performance", lambda: performance_report_tool(registry))
    registry.register("webhook", lambda action="status", url="", events="", name="": webhook_management_tool(registry, action, url, events, name))
    registry.register("webhook_status", lambda: webhook_management_tool(registry))
    registry.register("webhooks", lambda: webhook_management_tool(registry))
    registry.register("register_webhook", lambda action="register", url="", events="", name="": webhook_management_tool(registry, action, url, events, name))
    registry.register("scheduler", lambda action="list", name="", schedule="", command="", task_id="": task_scheduler_tool(registry, action, name, schedule, command, task_id))
    registry.register("task_scheduler", lambda action="list", name="", schedule="", command="", task_id="": task_scheduler_tool(registry, action, name, schedule, command, task_id))
    registry.register("schedule_task", lambda action="add", name="", schedule="", command="": task_scheduler_tool(registry, action, name, schedule, command))
    registry.register("list_tasks", lambda: task_scheduler_tool(registry))
    registry.register("proposal_ledger_view", lambda: proposal_ledger_tool(registry))
    registry.register("completed_improvements", lambda: completed_improvements_tool(registry))
    registry.register("anti_repeat_check", lambda title="", subsystems="": anti_repeat_tool(registry, title, subsystems))
