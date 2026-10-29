# Incident response investigation guide

## Principles
Investigations are evidence-based. State only what the retrieved records show, separate facts from hypotheses, and list what is missing. Automatic containment actions such as blocking an account, disabling a device or changing firewall rules must never be taken by the copilot; they require approval from a human analyst.

## Evidence requirements
For each alert collect: the alert details, authentication events for the user and the source IP, endpoint events for the user and device, and a time window around the alert. Record event IDs for every statement in the report.

## Correlation
Order events by time. Identify supporting evidence, conflicting evidence and missing evidence. A single indicator rarely proves compromise; several independent indicators raise confidence.

## Report contents
A report includes the alert summary, observed facts with event IDs, timeline, supporting evidence, conflicting evidence, missing evidence, uncertainties, recommended next checks and review status. Reports are handed to a human analyst for review.

## Escalation to DFIR
If an active compromise is likely, advise the analyst to engage the SISAP DFIR team through the Under Attack contact path.
