
# Email Notification Setup Guide

This guide will help you configure Gmail SMTP for sending real email notifications in the Confucius Institute Library Management System.

## Overview

The system supports sending automated email notifications for:
- **Due Date Reminders**: Sent 1-2 days before books are due
- **Overdue Notices**: Sent when books are past their due date with fine information
- **Test Emails**: Verify your email configuration is working

## Gmail SMTP Setup (Recommended)

### Prerequisites
- A Gmail account
- Access to Google Account settings

### Step 1: Enable 2-Factor Authentication

1. Go to your Google Account: https://myaccount.google.com/
2. Navigate to **Security** in the left sidebar
3. Under "How you sign in to Google", click **2-Step Verification**
4. Follow the prompts to enable 2-Step Verification (you'll need your phone)

### Step 2: Generate App Password

1. After enabling 2-Step Verification, go back to **Security**
2. Under "How you sign in to Google", click **2-Step Verification** again
3. Scroll down to **App passwords** (at the bottom)
4. Click **App passwords**
5. You may need to sign in again
6. In the "Select app" dropdown, choose **Mail**
7. In the "Select device" dropdown, choose **Other (Custom name)**
8. Enter a name like "Library System" or "Replit App"
9. Click **Generate**
10. **IMPORTANT**: Copy the 16-character password that appears (it will look like: `xxxx xxxx xxxx xxxx`)
11. Save this password securely - you won't be able to see it again!

### Step 3: Configure Replit Secrets

1. In your Replit workspace, click on **Tools** in the left sidebar
2. Select **Secrets** (or use the padlock icon)
3. Add the following secrets:

   **Secret 1:**
   - Key: `GMAIL_USER`
   - Value: Your full Gmail address (e.g., `your-email@gmail.com`)

   **Secret 2:**
   - Key: `GMAIL_APP_PASSWORD`
   - Value: The 16-character app password from Step 2 (remove spaces, e.g., `xxxxxxxxxxxxxxxx`)

   **Secret 3 (Optional):**
   - Key: `FROM_EMAIL`
   - Value: The email address to show as sender (usually same as GMAIL_USER)

4. Click **Add Secret** for each one

### Step 4: Restart Your Application

1. Stop the current running application (if running)
2. Click the **Run** button to restart with the new secrets
3. The dashboard should now show "Gmail SMTP Mode" instead of "Simulation Mode"

### Step 5: Test the Configuration

1. Navigate to the **Dashboard** in your application
2. Click the **Test Email** button in the Email Notification System section
3. Check the inbox of the admin email address
4. If you receive the test email, configuration is successful! ✅

## Using the Email System

### Sending Due Date Reminders

1. Go to the **Dashboard**
2. Click **Send Due Reminders** button
3. The system will send emails to students with books due in 1-2 days

### Sending Overdue Notices

1. Go to the **Dashboard**
2. Click **Send Overdue Notices** button
3. The system will send emails to students with overdue books and fine information

### Automated Scheduling (Optional)

For production environments, you can set up automated email sending using the included script:

```bash
# Send due reminders daily
python send_email_notifications.py --reminders

# Send overdue notices daily
python send_email_notifications.py --overdue

# Send both types
python send_email_notifications.py --all
```

You can schedule this using cron jobs or Replit's deployment features.

## Troubleshooting

### "No email credentials configured" Error

**Problem**: Secrets are not being read by the application

**Solution**:
- Verify secrets are named exactly: `GMAIL_USER` and `GMAIL_APP_PASSWORD`
- Check for extra spaces in the secret values
- Restart the application after adding secrets

### "Authentication failed" Error

**Problem**: Gmail is rejecting the app password

**Solution**:
- Verify 2-Step Verification is enabled on your Google Account
- Generate a new app password and update the `GMAIL_APP_PASSWORD` secret
- Ensure you're using the app password, NOT your regular Gmail password
- Remove any spaces from the app password

### Emails Not Being Received

**Problem**: Emails are marked as "sent" but not arriving

**Solution**:
- Check the spam/junk folder
- Verify the recipient email addresses in the student records are correct
- Check Gmail's sent folder to confirm emails were sent
- Ensure your Gmail account has not hit sending limits (Gmail allows ~500 emails/day)

### "Less secure app access" Message

**Problem**: Google suggests enabling "less secure apps"

**Solution**:
- **DO NOT** enable less secure apps - this is deprecated
- Use App Passwords instead (as described in Step 2)
- App Passwords are the official, secure method for SMTP access

## Alternative: SendGrid Setup

If you prefer SendGrid over Gmail:

1. Create a SendGrid account at https://sendgrid.com/
2. Generate an API key from the SendGrid dashboard
3. Add to Replit Secrets:
   - Key: `SENDGRID_API_KEY`
   - Value: Your SendGrid API key
   - Key: `FROM_EMAIL`
   - Value: Your verified sender email

## Email Limits

### Gmail SMTP Limits
- **500 emails per day** for regular Gmail accounts
- **2,000 emails per day** for Google Workspace accounts
- Rate limiting: ~100 emails per batch recommended

### SendGrid Limits
- Free tier: **100 emails per day**
- Paid tiers: Higher limits based on plan

## Security Best Practices

1. ✅ **Never share your app password** with anyone
2. ✅ **Never commit secrets** to version control
3. ✅ **Use Replit Secrets** for storing credentials
4. ✅ **Revoke app passwords** if compromised
5. ✅ **Monitor email logs** in the database for suspicious activity
6. ✅ **Change passwords regularly**

## Email Log Monitoring

All sent emails are logged in the `email_log` table with:
- Recipient email
- Subject and body
- Send timestamp
- Status (sent/failed)
- Error messages (if any)

You can query this table to monitor email delivery and troubleshoot issues.

## Support

If you encounter issues:
1. Check the application logs in the Console
2. Verify all secrets are correctly configured
3. Test with the **Test Email** button first
4. Review the `email_log` table for error messages

## Configuration Summary

| Secret Variable | Required | Example Value | Description |
|----------------|----------|---------------|-------------|
| `GMAIL_USER` | Yes (for Gmail) | `library@gmail.com` | Your Gmail email address |
| `GMAIL_APP_PASSWORD` | Yes (for Gmail) | `xxxxxxxxxxxxxxxx` | 16-character app password (no spaces) |
| `FROM_EMAIL` | Optional | `library@confucius.ac.ke` | Display email address for sender |
| `SENDGRID_API_KEY` | Yes (for SendGrid) | `SG.xxxxx...` | SendGrid API key (alternative to Gmail) |

## System Status Indicators

The dashboard shows the current email system status:
- **🟢 Gmail SMTP Mode**: Gmail is configured and ready
- **🟢 SendGrid Mode**: SendGrid is configured and ready
- **⚠️ Simulation Mode**: No credentials configured, emails logged but not sent
- **🔴 Failed**: Email sending encountered errors

---

**Last Updated**: October 2025  
**System Version**: 1.0
