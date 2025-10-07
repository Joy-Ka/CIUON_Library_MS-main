#!/usr/bin/env python3
"""
Automated Email Notification Script for Library System

This script can be run as a scheduled task (cron job) to automatically send:
1. Due date reminder emails (1-2 days before book due date)
2. Overdue notice emails (for books past their due date)

Usage:
    python send_email_notifications.py --reminders    # Send due date reminders
    python send_email_notifications.py --overdue      # Send overdue notices
    python send_email_notifications.py --all          # Send both types
"""

import argparse
import sys
from main import app
from utils.email_service import send_due_date_reminders, send_overdue_notices

def main():
    parser = argparse.ArgumentParser(description='Send automated email notifications')
    parser.add_argument('--reminders', action='store_true', help='Send due date reminder emails')
    parser.add_argument('--overdue', action='store_true', help='Send overdue notice emails')
    parser.add_argument('--all', action='store_true', help='Send all email notifications')
    
    args = parser.parse_args()
    
    # Use Flask app context
    with app.app_context():
        if args.all or args.reminders:
            print("Sending due date reminder emails...")
            sent_count = send_due_date_reminders()
            print(f"✓ Sent {sent_count} due date reminder emails")
        
        if args.all or args.overdue:
            print("Sending overdue notice emails...")
            sent_count = send_overdue_notices()
            print(f"✓ Sent {sent_count} overdue notice emails")
        
        if not (args.reminders or args.overdue or args.all):
            parser.print_help()
            sys.exit(1)

if __name__ == '__main__':
    main()
