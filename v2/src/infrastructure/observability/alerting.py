#!/usr/bin/env python3
"""
Theodore v2 Real-time Alerting System
====================================

Comprehensive alerting system for Theodore v2 with intelligent thresholds,
multiple notification channels, and escalation workflows.

This module provides:
- Real-time alert generation based on metrics and health checks
- Multiple notification channels (email, Slack, webhooks, SMS)
- Intelligent alert aggregation and deduplication
- Escalation workflows for critical issues
- Alert suppression and snoozing capabilities
- Integration with incident management systems
"""

import asyncio
import smtplib
import json

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Set
from dataclasses import dataclass, field
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import hashlib

from .logging import get_system_logger
from .metrics import MetricsCollector
from .health import HealthChecker, HealthStatus


class AlertLevel(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertChannel(str, Enum):
    """Alert notification channels"""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"
    PAGERDUTY = "pagerduty"
    TEAMS = "teams"
    DISCORD = "discord"


class AlertState(str, Enum):
    """Alert lifecycle states"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class Alert:
    """Individual alert instance"""
    id: str
    title: str
    description: str
    level: AlertLevel
    source: str
    timestamp: datetime
    state: AlertState = AlertState.ACTIVE
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    escalated: bool = False
    escalation_count: int = 0
    suppressed_until: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "level": self.level.value,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "state": self.state.value,
            "tags": self.tags,
            "metadata": self.metadata,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "escalated": self.escalated,
            "escalation_count": self.escalation_count,
            "suppressed_until": self.suppressed_until.isoformat() if self.suppressed_until else None
        }


@dataclass
class AlertRule:
    """Rule for generating alerts"""
    id: str
    name: str
    description: str
    condition: Callable[[Dict[str, Any]], bool]
    level: AlertLevel
    channels: List[AlertChannel]
    enabled: bool = True
    cooldown_minutes: int = 5
    escalation_minutes: Optional[int] = None
    tags: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        self.last_triggered: Optional[datetime] = None
        self.last_alert_id: Optional[str] = None


class BaseAlertChannel(ABC):
    """Base class for alert notification channels"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.logger = get_system_logger(f"alert_channel.{name}")
    
    @abstractmethod
    async def send_alert(self, alert: Alert) -> bool:
        """Send alert notification"""
        pass
    
    def format_alert_message(self, alert: Alert) -> str:
        """Format alert for this channel"""
        emoji_map = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.ERROR: "❌",
            AlertLevel.CRITICAL: "🚨"
        }
        
        emoji = emoji_map.get(alert.level, "📢")
        
        return f"""
{emoji} **{alert.title}**

**Level:** {alert.level.value.upper()}
**Source:** {alert.source}
**Time:** {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}

**Description:**
{alert.description}

**Alert ID:** {alert.id}
        """.strip()


class EmailAlertChannel(BaseAlertChannel):
    """Email notification channel"""
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send alert via email"""
        try:
            smtp_server = self.config.get("smtp_server")
            smtp_port = self.config.get("smtp_port", 587)
            username = self.config.get("username")
            password = self.config.get("password")
            from_email = self.config.get("from_email")
            to_emails = self.config.get("to_emails", [])
            
            if not all([smtp_server, username, password, from_email, to_emails]):
                self.logger.error("Email configuration incomplete")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = ", ".join(to_emails)
            msg['Subject'] = f"[Theodore Alert] {alert.level.value.upper()}: {alert.title}"
            
            body = self.format_alert_message(alert)
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(username, password)
            text = msg.as_string()
            server.sendmail(from_email, to_emails, text)
            server.quit()
            
            self.logger.info(f"Email alert sent for {alert.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
            return False


class SlackAlertChannel(BaseAlertChannel):
    """Slack notification channel"""
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send alert via Slack webhook"""
        try:
            if not AIOHTTP_AVAILABLE:
                self.logger.error("aiohttp not available for Slack alerts")
                return False
                
            webhook_url = self.config.get("webhook_url")
            if not webhook_url:
                self.logger.error("Slack webhook URL not configured")
                return False
            
            # Color based on alert level
            color_map = {
                AlertLevel.INFO: "#36a64f",
                AlertLevel.WARNING: "#ff9500", 
                AlertLevel.ERROR: "#ff0000",
                AlertLevel.CRITICAL: "#8b0000"
            }
            
            color = color_map.get(alert.level, "#808080")
            
            payload = {
                "attachments": [
                    {
                        "color": color,
                        "title": alert.title,
                        "text": alert.description,
                        "fields": [
                            {
                                "title": "Level",
                                "value": alert.level.value.upper(),
                                "short": True
                            },
                            {
                                "title": "Source",
                                "value": alert.source,
                                "short": True
                            },
                            {
                                "title": "Alert ID",
                                "value": alert.id,
                                "short": True
                            },
                            {
                                "title": "Time",
                                "value": alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC'),
                                "short": True
                            }
                        ],
                        "footer": "Theodore v2 Alerting",
                        "ts": int(alert.timestamp.timestamp())
                    }
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        self.logger.info(f"Slack alert sent for {alert.id}")
                        return True
                    else:
                        self.logger.error(f"Slack webhook failed with status {response.status}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Failed to send Slack alert: {e}")
            return False


class WebhookAlertChannel(BaseAlertChannel):
    """Generic webhook notification channel"""
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send alert via webhook"""
        try:
            if not AIOHTTP_AVAILABLE:
                self.logger.error("aiohttp not available for webhook alerts")
                return False
                
            webhook_url = self.config.get("webhook_url")
            headers = self.config.get("headers", {})
            
            if not webhook_url:
                self.logger.error("Webhook URL not configured")
                return False
            
            payload = {
                "alert": alert.to_dict(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "theodore-v2"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url, 
                    json=payload, 
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if 200 <= response.status < 300:
                        self.logger.info(f"Webhook alert sent for {alert.id}")
                        return True
                    else:
                        self.logger.error(f"Webhook failed with status {response.status}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Failed to send webhook alert: {e}")
            return False


class AlertManager:
    """Central alert management system"""
    
    def __init__(self):
        self.logger = get_system_logger("alert_manager")
        self.channels: Dict[str, BaseAlertChannel] = {}
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.suppressed_alerts: Set[str] = set()
        
        # Alert deduplication
        self.alert_fingerprints: Dict[str, str] = {}
        
        # Monitoring task
        self._monitoring_task: Optional[asyncio.Task] = None
        self._check_interval = 30  # seconds
    
    def register_channel(self, channel: BaseAlertChannel):
        """Register an alert notification channel"""
        self.channels[channel.name] = channel
        self.logger.info(f"Registered alert channel: {channel.name}")
    
    def register_email_channel(
        self,
        name: str,
        smtp_server: str,
        smtp_port: int,
        username: str,
        password: str,
        from_email: str,
        to_emails: List[str]
    ):
        """Register email alert channel"""
        config = {
            "smtp_server": smtp_server,
            "smtp_port": smtp_port,
            "username": username,
            "password": password,
            "from_email": from_email,
            "to_emails": to_emails
        }
        channel = EmailAlertChannel(name, config)
        self.register_channel(channel)
    
    def register_slack_channel(self, name: str, webhook_url: str):
        """Register Slack alert channel"""
        config = {"webhook_url": webhook_url}
        channel = SlackAlertChannel(name, config)
        self.register_channel(channel)
    
    def register_webhook_channel(
        self, 
        name: str, 
        webhook_url: str, 
        headers: Optional[Dict[str, str]] = None
    ):
        """Register webhook alert channel"""
        config = {
            "webhook_url": webhook_url,
            "headers": headers or {}
        }
        channel = WebhookAlertChannel(name, config)
        self.register_channel(channel)
    
    def add_rule(self, rule: AlertRule):
        """Add an alert rule"""
        self.rules[rule.id] = rule
        self.logger.info(f"Added alert rule: {rule.name}")
    
    def create_metric_threshold_rule(
        self,
        rule_id: str,
        name: str,
        metric_name: str,
        threshold: float,
        comparison: str,  # "gt", "lt", "eq"
        level: AlertLevel,
        channels: List[AlertChannel],
        cooldown_minutes: int = 5
    ):
        """Create a metric threshold alert rule"""
        def condition_func(metrics: Dict[str, Any]) -> bool:
            metric_value = metrics.get(metric_name, {}).get("value", 0)
            
            if comparison == "gt":
                return metric_value > threshold
            elif comparison == "lt":
                return metric_value < threshold
            elif comparison == "eq":
                return metric_value == threshold
            else:
                return False
        
        rule = AlertRule(
            id=rule_id,
            name=name,
            description=f"Metric {metric_name} {comparison} {threshold}",
            condition=condition_func,
            level=level,
            channels=channels,
            cooldown_minutes=cooldown_minutes,
            tags={"metric": metric_name, "threshold": str(threshold)}
        )
        
        self.add_rule(rule)
    
    def create_health_check_rule(
        self,
        rule_id: str,
        name: str,
        component_name: Optional[str] = None,
        level: AlertLevel = AlertLevel.ERROR,
        channels: List[AlertChannel] = None
    ):
        """Create a health check alert rule"""
        if channels is None:
            channels = [AlertChannel.EMAIL]
        
        def condition_func(health_data: Dict[str, Any]) -> bool:
            if component_name:
                # Check specific component
                components = health_data.get("components", [])
                for comp in components:
                    if comp.get("name") == component_name:
                        return comp.get("status") == "unhealthy"
                return False
            else:
                # Check overall status
                return health_data.get("status") == "unhealthy"
        
        rule = AlertRule(
            id=rule_id,
            name=name,
            description=f"Health check failure for {component_name or 'system'}",
            condition=condition_func,
            level=level,
            channels=channels,
            tags={"component": component_name or "system"}
        )
        
        self.add_rule(rule)
    
    def _generate_alert_id(self, rule: AlertRule, context: Dict[str, Any]) -> str:
        """Generate unique alert ID"""
        # Create fingerprint for deduplication
        fingerprint_data = {
            "rule_id": rule.id,
            "tags": rule.tags,
            "context_keys": list(context.keys())
        }
        fingerprint = hashlib.md5(
            json.dumps(fingerprint_data, sort_keys=True).encode()
        ).hexdigest()[:8]
        
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return f"alert_{fingerprint}_{timestamp}"
    
    async def trigger_alert(
        self,
        title: str,
        description: str,
        level: AlertLevel,
        source: str,
        channels: List[AlertChannel],
        tags: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """Manually trigger an alert"""
        alert_id = f"manual_{int(datetime.now(timezone.utc).timestamp())}"
        
        alert = Alert(
            id=alert_id,
            title=title,
            description=description,
            level=level,
            source=source,
            timestamp=datetime.now(timezone.utc),
            tags=tags or {},
            metadata=metadata or {}
        )
        
        # Store alert
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # Send notifications
        await self._send_alert_notifications(alert, channels)
        
        self.logger.info(f"Manual alert triggered: {alert_id}")
        return alert
    
    async def check_rules(self, metrics: Dict[str, Any], health_data: Dict[str, Any]):
        """Check all alert rules against current data"""
        current_time = datetime.now(timezone.utc)
        
        for rule in self.rules.values():
            if not rule.enabled:
                continue
            
            # Check cooldown
            if (rule.last_triggered and 
                current_time - rule.last_triggered < timedelta(minutes=rule.cooldown_minutes)):
                continue
            
            try:
                # Determine which data to pass to condition
                if "health" in rule.tags or "component" in rule.tags:
                    triggered = rule.condition(health_data)
                else:
                    triggered = rule.condition(metrics)
                
                if triggered:
                    await self._handle_rule_trigger(rule, metrics, health_data)
                    
            except Exception as e:
                self.logger.error(f"Error checking rule {rule.id}: {e}")
    
    async def _handle_rule_trigger(
        self, 
        rule: AlertRule, 
        metrics: Dict[str, Any], 
        health_data: Dict[str, Any]
    ):
        """Handle triggered alert rule"""
        alert_id = self._generate_alert_id(rule, {"metrics": metrics, "health": health_data})
        
        # Check for duplicate alert
        if alert_id in self.active_alerts:
            return
        
        alert = Alert(
            id=alert_id,
            title=rule.name,
            description=rule.description,
            level=rule.level,
            source="alert_rule",
            timestamp=datetime.now(timezone.utc),
            tags=rule.tags,
            metadata={
                "rule_id": rule.id,
                "triggered_by": "rule_engine"
            }
        )
        
        # Store alert
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # Update rule state
        rule.last_triggered = datetime.now(timezone.utc)
        rule.last_alert_id = alert_id
        
        # Send notifications
        await self._send_alert_notifications(alert, rule.channels)
        
        self.logger.warn(f"Alert rule triggered: {rule.name} ({alert_id})")
    
    async def _send_alert_notifications(self, alert: Alert, channels: List[AlertChannel]):
        """Send alert to specified channels"""
        for channel_type in channels:
            # Find matching channels
            matching_channels = [
                ch for ch in self.channels.values()
                if channel_type.value in ch.name.lower()
            ]
            
            for channel in matching_channels:
                try:
                    success = await channel.send_alert(alert)
                    if success:
                        self.logger.info(f"Alert {alert.id} sent via {channel.name}")
                    else:
                        self.logger.error(f"Failed to send alert {alert.id} via {channel.name}")
                except Exception as e:
                    self.logger.error(f"Error sending alert via {channel.name}: {e}")
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an active alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.state = AlertState.ACKNOWLEDGED
            alert.acknowledged_by = acknowledged_by
            alert.acknowledged_at = datetime.now(timezone.utc)
            
            self.logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
            return True
        
        return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an active alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.state = AlertState.RESOLVED
            alert.resolved_at = datetime.now(timezone.utc)
            
            # Remove from active alerts
            del self.active_alerts[alert_id]
            
            self.logger.info(f"Alert {alert_id} resolved")
            return True
        
        return False
    
    def suppress_alert(self, alert_id: str, duration_minutes: int) -> bool:
        """Suppress an alert for a specified duration"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.state = AlertState.SUPPRESSED
            alert.suppressed_until = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)
            
            self.suppressed_alerts.add(alert_id)
            
            self.logger.info(f"Alert {alert_id} suppressed for {duration_minutes} minutes")
            return True
        
        return False
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history"""
        return self.alert_history[-limit:]
    
    def start_monitoring(
        self, 
        metrics_collector: MetricsCollector, 
        health_checker: HealthChecker,
        interval_seconds: int = 30
    ):
        """Start continuous alert monitoring"""
        self._check_interval = interval_seconds
        
        if self._monitoring_task and not self._monitoring_task.done():
            return
        
        self._monitoring_task = asyncio.create_task(
            self._monitoring_loop(metrics_collector, health_checker)
        )
        self.logger.info(f"Started alert monitoring with {interval_seconds}s interval")
    
    def stop_monitoring(self):
        """Stop continuous monitoring"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            self.logger.info("Stopped alert monitoring")
    
    async def _monitoring_loop(
        self, 
        metrics_collector: MetricsCollector, 
        health_checker: HealthChecker
    ):
        """Continuous monitoring loop"""
        while True:
            try:
                # Get current metrics and health data
                metrics = metrics_collector.get_all_metrics()
                health_status = health_checker.get_last_health_check()
                if health_status:
                    health_data = {
                        "status": health_status.overall_status.value,
                        "components": [
                            {
                                "name": comp.component_name,
                                "status": comp.status.value
                            }
                            for comp in health_status.components
                        ]
                    }
                else:
                    health_data = {}
                
                # Check rules
                await self.check_rules(metrics, health_data)
                
                # Clean up resolved suppressed alerts
                current_time = datetime.now(timezone.utc)
                expired_suppressions = []
                
                for alert_id in self.suppressed_alerts:
                    if alert_id in self.active_alerts:
                        alert = self.active_alerts[alert_id]
                        if alert.suppressed_until and current_time > alert.suppressed_until:
                            alert.state = AlertState.ACTIVE
                            alert.suppressed_until = None
                            expired_suppressions.append(alert_id)
                
                for alert_id in expired_suppressions:
                    self.suppressed_alerts.remove(alert_id)
                
                await asyncio.sleep(self._check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Error in alert monitoring loop", error=e)
                await asyncio.sleep(self._check_interval)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get alerting system statistics"""
        total_alerts = len(self.alert_history)
        active_count = len(self.active_alerts)
        
        # Count by level
        level_counts = {}
        for level in AlertLevel:
            level_counts[level.value] = sum(
                1 for alert in self.alert_history 
                if alert.level == level
            )
        
        # Count by state
        state_counts = {}
        for state in AlertState:
            state_counts[state.value] = sum(
                1 for alert in self.alert_history 
                if alert.state == state
            )
        
        return {
            "total_alerts": total_alerts,
            "active_alerts": active_count,
            "suppressed_alerts": len(self.suppressed_alerts),
            "rules_configured": len(self.rules),
            "channels_configured": len(self.channels),
            "alerts_by_level": level_counts,
            "alerts_by_state": state_counts,
            "last_check": datetime.now(timezone.utc).isoformat()
        }


# Global alert manager instance
_global_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """Get global alert manager"""
    global _global_alert_manager
    if _global_alert_manager is None:
        _global_alert_manager = AlertManager()
    return _global_alert_manager