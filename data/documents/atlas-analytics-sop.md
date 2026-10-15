# Atlas Analytics Synthetic Operations SOP

Synthetic testing document only. Not a real operational policy.

## 1. Document control

Document ID: ATLAS-OPS-001. Version: 1.0. Effective date: 16 October 2026. Status: Active. Owner: Atlas Operations. This is a fully synthetic testing document. Atlas Analytics, all roles and all procedures described here are fictional. Do not use this document for real incidents.

## 2. Scope and incident classification

Atlas Analytics is a fictional dashboard service refreshed by a scheduled data pipeline. These procedures apply to Atlas Analytics only. Classify an incident as critical when the Atlas dashboard is unavailable to all users, or when its displayed data is more than 60 minutes behind the latest successfully ingested source timestamp. The support lead records the incident start time, affected dashboard, last successful refresh, and observed impact. The escalation clock starts when the incident is declared critical.

## 3. Critical incident escalation

For an Atlas Analytics critical incident that remains unresolved after 15 minutes, the support lead pages both the on-call incident commander and the Atlas service owner. The support lead opens a dedicated incident bridge and records the incident ID, impact, attempted mitigations, and blockers. The incident commander appoints a technical lead. If the incident commander has not acknowledged the page within 5 minutes of being paged, page the backup incident commander. Continue technical investigation while escalation proceeds.

## 4. Worked timing example

Illustrative example: incident ATLAS-DEMO-014 is declared critical at 09:00 WIB and remains unresolved. Page the incident commander and service owner at 09:15 WIB. If the incident commander still has not acknowledged at 09:20 WIB, page the backup incident commander. These are example timestamps, not a real incident record.

## 5. Stakeholder communications

The communications lead posts the initial stakeholder update within 10 minutes of critical incident declaration. Subsequent updates are posted every 20 minutes after the initial update until recovery is confirmed. Each update includes incident ID, impact, known facts, mitigation progress, and the next update time. If the recovery estimate is unknown, state that it is unknown. Exclude personal data, credentials, and confidential investigation details. For the 09:00 example, an initial update posted at 09:10 is followed by updates at 09:30 and 09:50 if the incident is ongoing.

## 6. Recovery approval and verification

Only the incident commander may authorize an Atlas pipeline rollback or data backfill. Before executing either action, the technical lead documents the last successful checkpoint, the affected data interval, the risk of duplicate records, and a validation plan. The Atlas service owner confirms that the dashboard is accessible and that displayed data is no more than 15 minutes behind the latest successfully ingested source timestamp. The incident commander then confirms recovery. The communications lead posts the final recovery notice.

## 7. Post-incident review

The support lead opens a post-incident review task within two business days after confirmed recovery. The review includes a timeline, impact, actions, contributing factors, and follow-up owners. This document does not define business-day holidays; do not infer a specific calendar due date without that information.

## 8. Information deliberately not specified

This document does not specify on-call phone numbers, personal email addresses, credentials, database restoration commands, contractual compensation, a monthly uptime SLA, a guaranteed recovery time, or a numeric recovery point objective (RPO). For those questions, state that the available Atlas document does not provide the information. Do not invent a value or substitute a general industry practice.
