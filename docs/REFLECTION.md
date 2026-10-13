\# Reflection: Responding to a Production Alert at 2:00 AM



My first step would be to identify the alert, affected target,

and start time. I would avoid assuming that every alert means

the application process is down.



I would distinguish application symptoms from monitoring failure.

If the probe scrape succeeds but probe\_success is 0, the HTTP check

failed. I would investigate the HTTP response, DNS, TLS, connectivity,

and probe settings. If up is 0, Prometheus cannot collect the probe

results, so the application's health is unknown. If up is 1 but

probe\_success is absent, I would investigate missing metrics or filtering.



I would check the application independently and inspect the Prometheus

target error. In my lab, stopping the application caused its metrics

scrape to fail while Blackbox Exporter continued reporting a failed

HTTP probe. Stopping the exporter instead caused a probe scrape failure.

These experiments helped me understand why the alerts need different

names and operator actions.



Next, I would assess customer impact using request rate, server-error

percentage, latency, and affected routes or instances. A working health

endpoint alone does not prove every feature works. Similarly, requests

that cannot reach the application may not appear in its request counters.



I would compare service symptoms with CPU, memory, filesystem space,

and database measurements. My database experiment showed that an SQL

query can fail while connection health remains successful. This prevents

me from treating every database error as a connectivity problem.



I would move from the metric spike to structured logs for the same

service and time window. UTC timestamps, routes, error codes, and

request IDs help identify the failed operations. Distributed traces

could show the path across services, but my current lab does not

implement tracing.



I would choose mitigation based on evidence: restore a stopped component,

correct a configuration, or involve the relevant owner. In production,

I would preserve evidence and follow approved deployment or rollback

procedures. I would escalate based on impact, uncertainty, and the speed

of error-budget consumption.



After mitigation, I would verify user-facing behavior, scrape status,

probe results, database health, and new error and latency measurements.

I would allow for the historical effects remaining in rate graphs.



Finally, I would document the timeline, impact, cause, recovery,

and follow-up actions. My main lesson is that a quiet alert or missing

metric does not prove health. Reliable operation requires measurement,

detection, investigation, response, recovery, and improvement.



This lab demonstrates the reliability workflow locally. It does not

prove production readiness or achievement of the proposed 30-day SLOs.

