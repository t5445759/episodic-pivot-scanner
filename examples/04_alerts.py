"""Example 4: Alerts Integration

This example demonstrates how to setup and use alerts.
"""

import asyncio
from src.alerts.handlers import AlertManager, EmailAlertHandler, SMSAlertHandler, WebhookAlertHandler
from datetime import datetime


async def main():
    """Run alerts example."""
    print("\n📢 Example 4: Alerts Integration\n")
    print("="*80)
    
    # Create alert manager
    alert_manager = AlertManager()
    
    # Add email handler (requires .env configuration)
    email_handler = EmailAlertHandler({
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'smtp_email': 'your-email@gmail.com',
        'smtp_password': 'your-app-password',
        'alert_recipients': ['recipient@example.com']
    })
    alert_manager.add_handler(email_handler)
    
    # Add webhook handler for Discord/Slack
    webhook_handler = WebhookAlertHandler(
        webhook_url='https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN'
    )
    alert_manager.add_handler(webhook_handler)
    
    print("\n✅ Alert handlers configured\n")
    
    # Create a sample alert
    alert = {
        'ticker': 'NVDA',
        'price': 425.50,
        'gap_pct': 12.50,
        'change_pct': 12.50,
        'relative_volume': 7.25,
        'volume': 45000000,
        'market_cap': 1050000000000,
        'market_cap_readable': '$1.05T',
        'sector': 'Technology',
        'score': 0.875,
        'timestamp': datetime.now()
    }
    
    print("📤 Sending alert for NVDA...\n")
    
    # Send alert
    success = await alert_manager.send_alert(alert)
    
    if success:
        print("\n✅ Alert sent successfully!")
    else:
        print("\n⚠️  Alert delivery had issues (check .env configuration)")
    
    # View alert history
    history = alert_manager.get_alert_history(limit=10)
    print(f"\n📋 Alert History: {len(history)} alerts")


if __name__ == "__main__":
    asyncio.run(main())
