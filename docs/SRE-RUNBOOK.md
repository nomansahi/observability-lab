\# SRE Runbook



\## Scope



This runbook covers the practice application, Prometheus,

Blackbox Exporter, Grafana, and embedded SQLite database.



The practice application is a temporary substitute.

The Vote application repository has not been supplied.



The lab uses Flask's development server and is not a production deployment.

Alerts are visible in Prometheus; external notifications are not configured.



\## Proposed reliability objectives



Measurement window: rolling 30 days.



| Measure | Objective | Measurement |

| --- | --- | --- |

| Availability | 99.9% | Successful HTTP health checks / scheduled checks |

| Latency | 95% within 500 ms | Requests in the 0.5-second histogram bucket / all measured requests |

| Server errors | At most 1% | HTTP 5xx requests / all measured requests |



Request measurements exclude /metrics and /health.

Deliberate failure endpoints are included during lab experiments.



These are proposed objectives, not demonstrated results.

The lab has not collected 30 days of evidence.



A health-endpoint check does not prove that every application

feature or database operation works.



Missing checks are unknown. Report successful, failed, and unknown

checks separately. Never count unknown checks as successful.



The scheduled-check denominator requires an expected schedule

independent of the collected samples. Averaging available

probe\_success samples alone can hide monitoring gaps.



The request metrics count requests that reach and complete in the app.

They cannot count requests that never reach it during an outage.



\## Error budgets



For a 99.9% availability objective:



\- Allowed unsuccessful fraction: 0.1%.

\- 30 days: 43,200 minutes.

\- Time-equivalent budget: 43.2 minutes, or 43 minutes 12 seconds.

\- At a 15-second schedule: 172,800 checks.

\- Check budget: 0.1% of scheduled checks.



Discrete check counts and sampling limit measurement precision.

The time equivalent is not an exact measurement of outage duration.



The latency budget allows 5% of measured requests above 500 ms.

The server-error budget allows 1% of measured requests to return 5xx.

Each objective has its own budget.



Example: a confirmed ten-minute outage consumes approximately

23.1% of the monthly availability time budget.



Unknown monitoring intervals do not prove application downtime,

but they prevent us from demonstrating that the objective was met.



\## 1. Alert received



Record the alert name, instance, start time, and investigation time.

Use UTC when comparing logs and metrics.



| Alert | Meaning |

| --- | --- |

| SiteProbeFailed | Scrape succeeded; HTTP probe failed |

| SiteProbeScrapeFailed | Prometheus could not collect probe metrics |

| SiteProbeResultMissing | Scrape succeeded; probe\_success was missing |



A failed probe can result from HTTP errors, DNS, TLS, or connectivity.

A monitoring failure leaves application health unknown.



\## 2. Initial checks



Run from the observability-lab folder:



```powershell

docker compose ps

```



Check Prometheus Targets at http://localhost:9090/targets.

Read the target error rather than relying only on the alert name.



Check the application directly:



```powershell

Invoke-WebRequest http://localhost:8000/health -UseBasicParsing

```



This tests access from the operator's machine.

It may differ from access through the Docker network.



\## 3. Dashboard investigation



Open the Observability Lab dashboard at http://localhost:3000.



Use a time range covering the incident and the preceding normal period.



Check:

\- Application metrics scrape status.

\- Probe scrape status and HTTP probe success.

\- Request rate, server errors, and p95 latency.

\- Process CPU and memory.

\- Filesystem used space.

\- SQLite connection health, query errors, and operation latency.



Elevated-error scenario:

1\. Confirm request traffic exists.

2\. Compare the error spike with latency and traffic changes.

3\. Check whether database errors rise at the same time.

4\. Check CPU, memory, and filesystem pressure.

5\. Determine which routes and instances are affected.

6\. Use matching logs to investigate the cause.



Healthy database connectivity does not imply every SQL query succeeds.

Process CPU and memory are not total host utilization.

Filesystem space is measured from inside the app container.



\## 4. Logs to inspect



Inspect relevant components:



```powershell

docker compose logs --since 10m app

docker compose logs --since 10m blackbox

docker compose logs --since 10m prometheus

```



Application request logs are JSON with:

timestamp, level, service, request\_id, method, route,

status, duration\_seconds, and error\_code.



Plain-text Flask access logs are also present.



The request\_id is returned in the X-Request-ID response header.

It is stored in logs, not metric labels, to avoid high cardinality.



\## 5. Metrics to query



Run these in Prometheus or Grafana, not PowerShell.



```promql

up{job="practice\_app"}

```



Can Prometheus collect application metrics?



```promql

up{job="site\_probe"}

```



Can Prometheus collect probe results?



```promql

probe\_success{job="site\_probe"}

```



Did the HTTP health check succeed?



```promql

sum by (instance, route, status) (

&#x20; rate(app\_http\_requests\_total{job="practice\_app"}\[5m])

)

```



Which instances, routes, and response statuses account for traffic?



```promql

instance:app\_http\_request\_duration\_seconds:p95

```



What is the recorded application p95 latency?



```promql

app\_db\_connection\_success{job="practice\_app"}

```



Did the latest SQLite connection check succeed?



```promql

sum(rate(app\_db\_queries\_total{job="practice\_app",result="error"}\[5m]))

```



How quickly are database query errors occurring?



Missing data and zero traffic must be investigated.

They are not automatically healthy results.



\## Telemetry correlation: metrics to logs



Start with the alert's instance and time window.

The practice\_app instance app:8000 maps to Compose service app.



For a current incident, isolate JSON errors from the last five minutes:



```powershell

docker compose logs --no-log-prefix --no-color --since 5m app |

&#x20;   Where-Object { $\_.TrimStart().StartsWith("{") } |

&#x20;   ForEach-Object { $\_ | ConvertFrom-Json } |

&#x20;   Where-Object { $\_.level -eq "ERROR" } |

&#x20;   ConvertTo-Json -Depth 5

```



For a historical spike, replace these UTC times with the incident window:



```powershell

docker compose logs --no-log-prefix --no-color --since "2026-10-12T14:55:00Z" --until "2026-10-12T15:05:00Z" app |

&#x20;   Where-Object { $\_.TrimStart().StartsWith("{") } |

&#x20;   ForEach-Object { $\_ | ConvertFrom-Json } |

&#x20;   Where-Object { $\_.status -ge 500 } |

&#x20;   ConvertTo-Json -Depth 5

```



To isolate database query failures, replace the final filter with:



```powershell

Where-Object { $\_.error\_code -eq "DATABASE\_QUERY\_FAILED" }

```



Compare log timestamps and routes with the metric spike.

Investigate a specific request using its request\_id.



Metrics identify patterns; logs provide request details.

Distributed traces would show timing across service calls.

This lab does not currently implement distributed tracing.

A request\_id alone is not a distributed trace.



Verified error-log evidence:

../evidence/application-error-logs.json



\## 6. Possible causes



\- Application container stopped or crashed.

\- HTTP endpoint returns an unsuccessful response.

\- Exporter stopped or unreachable.

\- Incorrect probe target, DNS, TLS, or module settings.

\- Metric filtering removes probe\_success.

\- Database query error or failed connection.

\- Resource pressure or slow application work.

\- Recent deployment or configuration change.



\## 7. Escalation criteria



Proposed lab policy:

\- Escalate immediately for confirmed widespread outage or data loss.

\- Escalate persistent elevated errors affecting users.

\- Escalate monitoring gaps that prevent impact assessment.

\- Involve the application owner for code or SQL failures.

\- Involve the infrastructure owner for connectivity or resource failures.



For a production deployment, document actual owners,

contact methods, and backup on-call coverage.



\## 8. Mitigation



Preserve relevant logs and the incident timeline.



For a deliberately stopped lab component:



```powershell

docker compose start app

docker compose start blackbox

```



Restore an incorrect target or remove the deliberate metric-drop rule,

then apply the configuration change.



For real incidents, choose mitigation based on evidence.

A restart alone does not establish or correct the root cause.



If budget consumption is rapid, prioritize mitigation and pause

nonessential releases. If a budget is exhausted, prioritize

reliability fixes under an agreed team policy.



\## 9. Recovery



Confirm:

\- Application metrics scrape status is 1.

\- Probe scrape status is 1.

\- HTTP probe success is 1.

\- Database connection health is 1.

\- Relevant alerts clear.

\- New request errors and latency return to acceptable levels.

\- A user-facing request works.



Five-minute rate graphs may retain the incident's effects after recovery.

Observe several scrape and evaluation cycles.



\## 10. Post-incident review



Record:

\- Customer impact and affected functions.

\- Incident start, detection, mitigation, and recovery times.

\- Evidence supporting the cause.

\- Error-budget consumption and monitoring gaps.

\- What worked and what delayed diagnosis.

\- Follow-up actions, owners, and deadlines.



For this lab:

MTTD = detection time minus incident start.

MTTR = restoration time minus incident start.

State this definition when reporting the measurements.



Use a blameless review focused on improving the system.

Add regression tests for newly discovered failure modes.

