"""Alert management and delivery system."""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime
import json


class AlertHandler(ABC):
    """Abstract base class for alert handlers."""
    
    @abstractmethod
    async def send_alert(self, alert: Dict) -> bool:
        """Send an alert.
        
        Args:
            alert: Dictionary containing alert details
            
        Returns:
            True if sent successfully, False otherwise
        """
        pass


class EmailAlertHandler(AlertHandler):
    """Send alerts via email."""
    
    def __init__(self, smtp_config: Dict):
        """Initialize email alert handler.
        
        Args:
            smtp_config: Dict with smtp_server, smtp_port, smtp_email, smtp_password
        """
        self.smtp_server = smtp_config.get('smtp_server')
        self.smtp_port = smtp_config.get('smtp_port')
        self.smtp_email = smtp_config.get('smtp_email')
        self.smtp_password = smtp_config.get('smtp_password')
        self.recipients = smtp_config.get('alert_recipients', [])
    
    async def send_alert(self, alert: Dict) -> bool:
        """Send alert via email."""
        if not self.recipients or not self.smtp_email:
            print("Email config incomplete, skipping email alert")
            return False
        
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Build email
            msg = MIMEMultipart()
            msg['From'] = self.smtp_email
            msg['To'] = ', '.join(self.recipients)
            msg['Subject'] = self._format_subject(alert)
            
            body = self._format_body(alert)
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_email, self.smtp_password)
                server.send_message(msg)
            
            print(f"✉️  Email alert sent to {self.recipients}")
            return True
            
        except Exception as e:
            print(f"❌ Error sending email alert: {e}")
            return False
    
    def _format_subject(self, alert: Dict) -> str:
        """Format email subject line."""
        ticker = alert.get('ticker', 'UNKNOWN')
        gap = alert.get('gap_pct', 0)
        return f"🚀 EPISODIC PIVOT ALERT: {ticker} gapping {gap:.1f}%"
    
    def _format_body(self, alert: Dict) -> str:
        """Format email body as HTML."""
        ticker = alert.get('ticker', 'N/A')
        price = alert.get('price', 0)
        gap_pct = alert.get('gap_pct', 0)
        change_pct = alert.get('change_pct', 0)
        rel_vol = alert.get('relative_volume', 0)
        volume = alert.get('volume', 0)
        market_cap = alert.get('market_cap_readable', 'N/A')
        sector = alert.get('sector', 'Unknown')
        score = alert.get('score', 0)
        timestamp = alert.get('timestamp', datetime.now())
        
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #2ecc71;">🚀 EPISODIC PIVOT ALERT</h2>
                
                <table style="border-collapse: collapse; width: 100%;">
                    <tr style="background-color: #f2f2f2;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><b>Ticker</b></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{ticker}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><b>Price</b></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">${price:.2f}</td>
                    </tr>
                    <tr style="background-color: #f2f2f2;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><b>Gap %</b></td>
                        <td style="padding: 10px; border: 1px solid #ddd; color: #2ecc71;"><b>{gap_pct:.2f}%</b></td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><b>Change %</b></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{change_pct:.2f}%</td>
                    </tr>
                    <tr style="background-color: #f2f2f2;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><b>Relative Volume</b></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{rel_vol:.2f}x</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><b>Volume</b></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{volume:,.0f}</td>
                    </tr>
                    <tr style="background-color: #f2f2f2;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><b>Market Cap</b></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{market_cap}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><b>Sector</b></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{sector}</td>
                    </tr>
                    <tr style="background-color: #f2f2f2;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><b>Score</b></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{score:.3f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><b>Timestamp</b></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{timestamp}</td>
                    </tr>
                </table>
                
                <p style="margin-top: 20px; color: #7f8c8d;">
                    <small>Episodic Pivot Scanner - Research & Paper Trading Only</small>
                </p>
            </body>
        </html>
        """
        return html


class SMSAlertHandler(AlertHandler):
    """Send alerts via SMS using Twilio."""
    
    def __init__(self, twilio_config: Dict):
        """Initialize SMS alert handler.
        
        Args:
            twilio_config: Dict with account_sid, auth_token, from, to numbers
        """
        self.account_sid = twilio_config.get('twilio_account_sid')
        self.auth_token = twilio_config.get('twilio_auth_token')
        self.from_number = twilio_config.get('twilio_from')
        self.to_number = twilio_config.get('twilio_to')
    
    async def send_alert(self, alert: Dict) -> bool:
        """Send alert via SMS."""
        if not self.account_sid or not self.auth_token:
            print("Twilio config incomplete, skipping SMS alert")
            return False
        
        try:
            from twilio.rest import Client
            
            client = Client(self.account_sid, self.auth_token)
            
            # Build SMS message
            message = self._format_message(alert)
            
            sms = client.messages.create(
                body=message,
                from_=self.from_number,
                to=self.to_number
            )
            
            print(f"📱 SMS alert sent to {self.to_number}")
            return True
            
        except Exception as e:
            print(f"❌ Error sending SMS alert: {e}")
            return False
    
    def _format_message(self, alert: Dict) -> str:
        """Format SMS message (keep it short)."""
        ticker = alert.get('ticker', 'N/A')
        price = alert.get('price', 0)
        gap_pct = alert.get('gap_pct', 0)
        rel_vol = alert.get('relative_volume', 0)
        score = alert.get('score', 0)
        
        return f"🚀 {ticker} ${price:.2f} GAP:{gap_pct:.1f}% VOL:{rel_vol:.1f}x SCORE:{score:.2f}"


class WebhookAlertHandler(AlertHandler):
    """Send alerts via webhook to external services."""
    
    def __init__(self, webhook_url: str):
        """Initialize webhook alert handler.
        
        Args:
            webhook_url: URL to POST alerts to (Discord, Slack, etc.)
        """
        self.webhook_url = webhook_url
    
    async def send_alert(self, alert: Dict) -> bool:
        """Send alert via webhook."""
        if not self.webhook_url:
            return False
        
        try:
            import httpx
            
            # Format payload
            payload = self._format_payload(alert)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(self.webhook_url, json=payload)
                
                if response.status_code in [200, 204]:
                    print(f"🔗 Webhook alert sent successfully")
                    return True
                else:
                    print(f"❌ Webhook returned status {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error sending webhook alert: {e}")
            return False
    
    def _format_payload(self, alert: Dict) -> Dict:
        """Format alert as JSON payload for webhook."""
        return {
            'ticker': alert.get('ticker'),
            'price': alert.get('price'),
            'gap_pct': alert.get('gap_pct'),
            'change_pct': alert.get('change_pct'),
            'relative_volume': alert.get('relative_volume'),
            'volume': alert.get('volume'),
            'market_cap': alert.get('market_cap'),
            'sector': alert.get('sector'),
            'score': alert.get('score'),
            'timestamp': str(alert.get('timestamp')),
            'alert_type': 'episodic_pivot'
        }


class AlertManager:
    """Manages multiple alert handlers and delivery."""
    
    def __init__(self):
        """Initialize alert manager."""
        self.handlers: List[AlertHandler] = []
        self.alert_history: List[Dict] = []
    
    def add_handler(self, handler: AlertHandler):
        """Add an alert handler.
        
        Args:
            handler: Instance of AlertHandler subclass
        """
        self.handlers.append(handler)
    
    async def send_alert(self, alert: Dict) -> bool:
        """Send alert through all configured handlers.
        
        Args:
            alert: Dictionary containing alert details
            
        Returns:
            True if any handler succeeded, False if all failed
        """
        if not self.handlers:
            print("⚠️  No alert handlers configured")
            return False
        
        results = []
        for handler in self.handlers:
            try:
                result = await handler.send_alert(alert)
                results.append(result)
            except Exception as e:
                print(f"❌ Error with handler {handler.__class__.__name__}: {e}")
                results.append(False)
        
        # Store in history
        self.alert_history.append({
            'alert': alert,
            'timestamp': datetime.now(),
            'success': any(results)
        })
        
        return any(results)
    
    def get_alert_history(self, limit: int = 100) -> List[Dict]:
        """Get recent alert history.
        
        Args:
            limit: Maximum number of alerts to return
            
        Returns:
            List of alert history dictionaries
        """
        return self.alert_history[-limit:]
