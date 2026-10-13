# Observability Lab



A local learning lab for metrics, alert reliability, dashboards,

structured logs, and incident response.



The practice application temporarily substitutes for the Vote application,

whose repository was not supplied.



## Requirements



- Docker Desktop running with Linux containers.

- Docker Compose.

- PowerShell.

- Internet access for the initial image and dependency downloads.



## Start



Open PowerShell in the observability-lab folder:



```powershell

docker compose up -d --build

docker compose ps

```



## Interfaces



| Component | Browser address |
| --- | --- |
| Application | http://localhost:8000 |
| Application health | http://localhost:8000/health |
| Application metrics | http://localhost:8000/metrics |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |



## Grafana setup



On a fresh Grafana volume, log in with admin/admin and set a new password.



Add a Prometheus data source with this server URL:



    http://prometheus:9090



Import grafana/dashboard.json.

Select the Prometheus data source if prompted.



The dashboard is named Observability Lab.



## Application endpoints



| Endpoint | Behavior |
| --- | --- |
| / | Successful request |
| /health | HTTP health check |
| /metrics | Prometheus metrics |
| /fail | Deliberate HTTP 500 |
| /slow | Deliberate one-second delay |
| /db | Successful SQLite query |
| /db-fail | Deliberate SQL error and HTTP 500 |



Health and metrics requests are excluded from application request statistics.



## Generate traffic



Run in PowerShell:



```powershell

1..20 | ForEach-Object {

    Invoke-WebRequest http://localhost:8000/ -UseBasicParsing | Out-Null

    Invoke-WebRequest http://localhost:8000/db -UseBasicParsing | Out-Null



    try {

        Invoke-WebRequest http://localhost:8000/fail -UseBasicParsing -ErrorAction Stop | Out-Null

    } catch {}



    try {

        Invoke-WebRequest http://localhost:8000/db-fail -UseBasicParsing -ErrorAction Stop | Out-Null

    } catch {}



    Invoke-WebRequest http://localhost:8000/slow -UseBasicParsing | Out-Null

    Start-Sleep -Seconds 1

}

```



The errors are intentional.

Allow time for scraping and rule evaluation, then refresh Grafana.



Use Last 15 minutes to view recent traffic.

Short bursts before a counter's first scrape may not be visible

as increases between samples.



## Alert rules



| Condition | Alert |
| --- | --- |
| up=1, probe_success=0 | SiteProbeFailed |
| up=0 | SiteProbeScrapeFailed |
| up=1, probe_success absent | SiteProbeResultMissing |



Healthy probes produce no alerts.

All three rules use for: 0m for the lab.



Scrapes and evaluations run every 15 seconds.

Alerts fire at evaluations, not immediately when a command runs.



## Reproduce failures



### 1. Monitoring failure



```powershell

docker compose stop blackbox

```



Expect probe up=0, probe_success absent, and SiteProbeScrapeFailed.



Restore:



```powershell

docker compose start blackbox

```



### 2. Application unavailable



```powershell

docker compose stop app

```



Expect:

- up for practice_app = 0.

- up for site_probe = 1.

- probe_success = 0.

- SiteProbeFailed fires.



Restore:



```powershell

docker compose start app

```



### 3. Missing probe metric



Under the site_probe job in prometheus/prometheus.yml, add:



```yaml

    metric_relabel_configs:

      - source_labels: [__name__]

        regex: probe_success

        action: drop

```



Apply:



```powershell

docker compose restart prometheus

```



Expect probe up=1, probe_success absent, and SiteProbeResultMissing.



Restore by removing that whole section and restarting Prometheus.



Older samples may remain visible temporarily after a restart.

Check the current Targets page and allow several evaluation cycles.



### 4. HTTP and database query errors



Request /fail or /db-fail while the app remains running.



These produce HTTP 500 responses and structured error logs.

They appear in request/error panels.



The current probe checks /health, so these requests alone do not

trigger SiteProbeFailed. There is no high-error-rate alert configured.



SQLite connection health may remain 1 during SQL statement failures.



## Validate rules and configuration



```powershell

docker compose exec prometheus promtool check config /etc/prometheus/prometheus.yml

```



Run the eight alert-test scenarios:



```powershell

docker compose run --rm --no-deps --entrypoint /bin/promtool -v "${PWD}:/lab:ro" -w /lab/tests prometheus test rules alert-tests.yml

```



The tests verify expected alerts and alerts that must remain quiet.



## Inspect structured error logs



```powershell

docker compose logs --no-log-prefix --no-color --since 5m app |

    Where-Object { $_.TrimStart().StartsWith("{") } |

    ForEach-Object { $_ | ConvertFrom-Json } |

    Where-Object { $_.level -eq "ERROR" } |

    ConvertTo-Json -Depth 5

```



Historical time-window filters are in docs/SRE-RUNBOOK.md.



## Documentation



- docs/PROMQL-RESEARCH.md: explained diagnostic queries.

- docs/RESEARCH-NOTES.md: research across five areas.

- docs/ALERT-DESIGN.md: rule behavior and tests.

- docs/GRAFANA-DASHBOARD.md: panels and investigations.

- docs/FAILURE-SCENARIOS.md: original failure experiments.

- docs/ARCHITECTURE.md: components and data flow.

- docs/SRE-RUNBOOK.md: proposed SLOs and incident response.

- docs/REFLECTION.md: response to a production alert.

- docs/AI-USAGE.md: AI assistance and prompt record.



Evidence is stored in evidence/.

The exported dashboard is grafana/dashboard.json.



## Storage and stopping



Prometheus and Grafana use named Docker volumes.



Stop without deleting stored data:



```powershell

docker compose stop

```



SQLite demonstration data is inside the app container and may be lost

when it is recreated. Application counters reset when the process restarts.



## Versions



- Prometheus and promtool: 3.15.0.

- Blackbox Exporter: 0.27.0.

- Grafana: 13.2.3.

- Python base image: 3.12.12-slim.

- Flask: 3.1.2.

- prometheus-client: 0.23.1.



## Limitations



This is a local lab using Flask's development server.

It is not a production deployment.



CPU and memory describe the app process.

Filesystem metrics describe the filesystem visible inside Docker.

SQLite is embedded rather than a separate database service.



No Alertmanager, external notifications, or distributed tracing backend

is configured. Prometheus outages require an independent external check.



SLOs are proposed; 30-day compliance has not been demonstrated.

No-data intervals and missing targets require explicit investigation.


