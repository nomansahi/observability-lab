\# Grafana Dashboard



\## Setup



Dashboard: Observability Lab

Grafana version: 13.2.3

Prometheus data source: http://prometheus:9090



Exported configuration: grafana/dashboard.json



The practice application temporarily substitutes for the Vote application.



\## Panels



| Panel | Operator question |

| --- | --- |

| Probe scrape status | Can Prometheus collect probe results? |

| HTTP probe success | Did the application's HTTP health check succeed? |

| HTTP probe duration | How long did the complete probe take? |

| Firing probe alerts | Which probe alerts are firing? |

| Application metrics scrape status | Can Prometheus collect application metrics? |

| Application request rate | How much traffic is arriving? |

| Application server error percentage | What fraction of requests return HTTP 5xx? |

| Application p95 request latency | How slow are the slower requests? |

| Application process CPU | How much CPU does the process use? |

| Application process memory | How much resident memory does it use? |

| App filesystem used space | How much filesystem space is used? |

| SQLite connection health | Can the app connect and execute SELECT 1? |

| Database query error rate | How quickly are database operations failing? |

| Database p95 operation latency | How long do database operations take? |



Status and firing-alert panels use instant queries.

Trend panels use range queries.



\## RED and USE



Request rate, errors, and latency implement the RED view.



Process CPU, memory, and filesystem space provide part of a resource view.

They do not provide full host monitoring or saturation measurements.



\## Tested investigations



\### Monitoring failure



When Blackbox Exporter stopped:

\- Probe scrape status became 0.

\- HTTP probe success was absent.

\- SiteProbeScrapeFailed fired.



The application's health was unknown from the probe results.

Restarting the exporter restored collection.



Evidence: ../evidence/grafana-scrape-failure.png



\### Application stopped



When the application stopped:

\- Application metrics scrape status became 0.

\- Probe scrape status remained 1.

\- HTTP probe success became 0.

\- SiteProbeFailed fired.



Blackbox Exporter remained available and reported the failed HTTP check.

Starting the application restored the status panels.



Evidence: ../evidence/grafana-application-stopped.png



\### Database query errors



Deliberate requests to /db-fail caused SQL errors.

The database query error rate showed failures while connection health

remained 1.



A failed SQL statement does not necessarily mean the database

connection is broken.



Evidence: ../evidence/grafana-database-query-errors.png



\## Elevated application errors: dashboard investigation



1\. Select a time range covering the spike and the preceding normal period.

2\. Confirm request traffic exists.

3\. Check application and probe scrape status.

4\. Compare HTTP errors with request rate and p95 latency.

5\. Check whether database errors or latency rise at the same time.

6\. Compare CPU, memory, and filesystem-space trends.

7\. Use PromQL grouped by route, status, and instance to narrow the scope.

8\. Determine the next investigation from these observations.



The dashboard identifies symptoms and possible dependencies.

Logs or further checks are needed to establish the cause.



\## Interpretation limits



No data is different from zero.



No rows in the firing-alert table means no matching alerts are firing.

It does not independently prove the monitoring system is healthy.



With no requests, error percentages and latency quantiles can be undefined.



Histogram quantiles are estimates affected by bucket spacing.

Database operation latency includes connection setup and failed operations.



CPU and memory describe the application process.

Filesystem metrics describe the filesystem visible at /app inside Docker.

SQLite is embedded, not a separate database server.



\## Import



Import grafana/dashboard.json into Grafana.

Select the configured Prometheus data source if prompted.

Use current evaluation time for status panels.

