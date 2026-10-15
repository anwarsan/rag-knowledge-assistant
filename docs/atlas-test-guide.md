# Atlas synthetic SOP test guide

Synthetic examples only. These are expected behaviors for manual review, not recorded model results. The Markdown SOP is indexed; the answer guide is outside data/documents and must not be added to the corpus.

After the app redeploys, select Hybrid RAG (OpenAI) and click Build / check vector index. The corpus fingerprint changes, so old indexes are not used for the new corpus. Source references should point to documents/atlas-analytics-sop.md with heading locations and version 1.0. The PDF supplied separately is a reading copy, not a second indexed copy.

| Question | Expected behavior | Evidence |
| --- | --- | --- |
| When is an Atlas Analytics incident classified as critical? | All-user dashboard outage OR data more than 60 minutes behind latest successfully ingested source timestamp. | Section 2 |
| Atlas is declared critical at 09:00 WIB and remains unresolved. When do we page the commander and when do we contact the backup if there is no acknowledgement? | Commander and owner at 09:15; backup commander at 09:20. | Sections 3-4 |
| For Atlas, what are the escalation steps and how often should stakeholder updates be posted? | Escalate after 15 minutes; initial update within 10 minutes of declaration; subsequent updates every 20 minutes after initial update. Cite both relevant sections. | Sections 3 and 5 |
| Who may approve an Atlas pipeline rollback, and what must be verified before recovery is confirmed? | Incident commander authorizes rollback; service owner verifies access and freshness lag no more than 15 minutes, then commander confirms recovery. | Section 6 |
| What is the exact monthly uptime SLA for Atlas Analytics? | Withhold numeric answer; document does not specify SLA. | Section 8 |
| What phone number should I call to reach the Atlas incident commander? | Withhold contact details; no number provided. | Section 8 |

Check correct facts and source references separately. A plausible answer with a valid quote can still omit conditions or draw an unsupported conclusion. Try paraphrases and compare local evidence preview with full RAG. A failed retrieval should be diagnosed before changing the generation prompt.
