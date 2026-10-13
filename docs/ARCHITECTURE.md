\# Observability Lab Architecture



\## Components



| Component | Role |

| --- | --- |

| Practice application | Serves HTTP requests and exposes application metrics |

| SQLite | Embedded database used by demonstration queries |

| Blackbox Exporter | Performs HTTP health checks |

| Prometheus | Scrapes metrics, evaluates rules, and stores time series |

| Grafana | Queries Prometheus and displays dashboards |

| Docker logs | Stores application output for operator investigation |



The practice application temporarily substitutes for the unspecified

Vote application. SQLite runs inside the application container.



\## Data flow



```mermaid

flowchart TD

&#x20;   Operator\["Operator"]

&#x20;   Grafana\["Grafana"]

&#x20;   Prometheus\["Prometheus"]

&#x20;   Blackbox\["Blackbox Exporter"]

&#x20;   App\["Practice app and SQLite"]

&#x20;   Logs\["Application JSON logs"]



&#x20;   Operator -->|Views dashboards| Grafana

&#x20;   Grafana -->|PromQL queries| Prometheus

&#x20;   Prometheus -->|Scrapes /metrics| App

&#x20;   Prometheus -->|Scrapes /probe with target URL| Blackbox

&#x20;   Blackbox -->|HTTP GET /health| App

&#x20;   App -->|Writes request events| Logs

&#x20;   Operator -->|Filters using PowerShell| Logs

```



Arrows describe requests or actions. Metric responses return to

Prometheus, which stores the collected samples.



\## Collection and evaluation



Prometheus scrapes and evaluates rules every 15 seconds.



The practice\_app job scrapes app:8000/metrics.



The site\_probe job scrapes blackbox:9115/probe.

It passes http://app:8000/health as the target and uses

the http\_2xx module.



Recording rules store request rate, server-error rate,

and estimated p95 latency.



Three alert rules distinguish:

\- Failed HTTP checks.

\- Failed probe scrapes.

\- Missing probe results during successful scrapes.



\## Addresses



Inside the Docker network:

\- Prometheus: http://prometheus:9090

\- Blackbox Exporter: http://blackbox:9115

\- Application: http://app:8000



From the operator's browser:

\- Prometheus: http://localhost:9090

\- Grafana: http://localhost:3000

\- Application: http://localhost:8000



localhost refers to the machine or container making the request.

Grafana therefore uses prometheus:9090 rather than localhost:9090.



\## Storage



Prometheus data uses the prometheus-data Docker volume.

Grafana settings and dashboards use the grafana-data volume.



SQLite demonstration data is inside the application container

and can be lost when that container is recreated.



Configuration files and exported evidence are in the project folder.



\## Limitations



This is a local learning lab with a Flask development server.



CPU and memory metrics describe the application process.

Disk metrics describe the filesystem visible inside its container.



Logs are inspected using Docker and PowerShell.

There is no centralized log service or distributed tracing backend.



Alertmanager and external notification delivery are not configured.

Prometheus alerts are inspected through its web interface.



Prometheus cannot report its own complete outage while stopped.

Production monitoring needs an independent check of the monitoring system.

