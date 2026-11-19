# Company Data Handling & Privacy Policy
Owner: Information Security & Data Governance (data-governance@company.com)
Last-Updated: 2026-02-15

## Data Classification Tiers
Information assets are classified into four tiers: Public (freely disclosable), Internal (company staff only), Confidential (restricted to specific departments e.g., payroll, customer contracts), and Strictly Confidential (PII, authentication secrets, encryption keys, unreleased financial reports). Strictly Confidential assets must always be encrypted at rest and in transit.

## Customer Data Protection and Privacy
Customer Personally Identifiable Information (PII) must be processed strictly in accordance with GDPR, DPDP Act, and enterprise privacy commitments. Production customer databases must never be exported, replicated, or restored into local development machines or staging environments without complete anonymization and masking.

## Access Control and Principle of Least Privilege
Access to production systems, customer databases, and sensitive source code is granted on a strict need-to-know basis following the Principle of Least Privilege. Privileged production access requires documented manager approval, just-in-time access granting, and mandatory multi-factor authentication. Access permissions are audited and re-certified on a quarterly basis.

## Data Retention and Secure Disposal
Corporate and customer records must be retained in accordance with statutory requirements (financial records: 7 years, employee files: 5 years post-exit). Physical hard drives and SSDs scheduled for decommission must undergo cryptographic erasure and physical shredding with a Certificate of Destruction issued by certified vendors.

## Security Incident Notification Requirements
Any suspected data breach, credential compromise, or unintended data exposure must be reported to `security-incident@company.com` within 1 hour of discovery. The Computer Security Incident Response Team (CSIRT) assesses the severity and initiates customer and regulatory notifications within required 72-hour statutory windows.
