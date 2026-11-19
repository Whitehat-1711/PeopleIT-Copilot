# Company IT Security & Hardware Policy
Owner: IT Infrastructure & Security (it-security@company.com)
Last-Updated: 2026-02-01

## Password and Multi-Factor Authentication (MFA)
All corporate accounts (Google Workspace, Slack, GitHub, Jira, and AWS) must use unique passwords of at least 14 characters containing uppercase letters, lowercase letters, numbers, and special symbols. Passwords must be rotated every 90 days and cannot reuse any of the last 5 passwords. Phishing-resistant Multi-Factor Authentication (hardware security key or approved authenticator app) is mandatory for all corporate logins; SMS-based OTP is not permitted for production systems.

## VPN and Network Access
Remote access to internal databases, staging environments, and private repositories requires connecting through the corporate WireGuard VPN client using a company-issued certificate. Split-tunneling is disabled by default for production access. Personal unmanaged devices (BYOD laptops or home desktops) are strictly prohibited from connecting to the corporate VPN or downloading source code.

## Hardware Provisioning and Replacement
Standard developer machines are MacBook Pro 16-inch laptops, while business and operations roles are issued Dell XPS 15 or ThinkPad X1 Carbon laptops. Company laptops are eligible for hardware refresh every 36 months. Any lost, stolen, or physically damaged device must be reported immediately to the IT Security Helpdesk (`it-helpdesk@company.com`) within 24 hours so remote wipe and device revocation can be initiated.

## Approved Software and AI Tool Usage
Employees may only install software from the pre-approved Self-Service Software Catalog. Unapproved browser extensions, pirated software, and unauthorized remote desktop utilities are strictly prohibited. When using external generative AI tools, employees must never paste customer PII, API keys, database credentials, proprietary source code, or confidential financial records into public prompts.

## Endpoint Security and Encryption
All company laptops must run full-disk encryption (FileVault on macOS, BitLocker on Windows) and the corporate Endpoint Detection and Response (EDR) agent at all times. Copying company data onto unencrypted USB flash drives or personal cloud storage accounts (personal Google Drive, Dropbox, or iCloud) is a severe security violation and triggers automatic DLP alerts.

## IT Helpdesk Support and SLAs
For account lockouts, VPN certificate renewals, or hardware failures, employees should raise a ticket on the internal IT Service Desk portal. Priority 1 (P1) incidents—such as complete workstation failure or suspected credential compromise—have a 1-hour response SLA, while standard software access requests (Priority 3) are resolved within 2 business days.
