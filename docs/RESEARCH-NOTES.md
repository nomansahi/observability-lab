\# Research Notes



\## 1. Prometheus metrics and PromQL



Prometheus pulls metrics from configured targets.

An exporter exposes measurements in a format Prometheus can scrape.

Blackbox Exporter instead performs a requested check and exposes its result.



A time series is identified by its metric name and complete label set.

Changing the instance label creates a different series.



Cardinality is the number of distinct series.

Unbounded labels such as request IDs or full user-supplied URLs

can create excessive cardinality. Our request IDs stay in logs.



\### Metric types



\- Counter: cumulative events, such as HTTP requests. Resets on restart.

\- Gauge: a current value that can rise or fall, such as memory usage.

\- Histogram: counts observations in buckets and provides count and sum.

\- Summary: provides count and sum and may calculate quantiles in the client.



Classic histogram buckets can be aggregated before estimating quantiles.

Client-calculated summary quantiles generally cannot be combined across instances.

The Python client's Summary does not expose calculated quantiles.



\### Vectors and functions



An instant vector contains one selected sample per series at an evaluation time.

A range vector contains samples over a window, such as requests\_total\[5m].



\- rate(): estimated average counter increase per second over the window.

\- increase(): estimated total counter increase over the window.

\- irate(): rate based on the last two samples; sensitive to short changes.

\- histogram\_quantile(): estimates a percentile from histogram data.



Use rate before aggregation so counter resets are handled per series.

Prefer rate over irate for alerts requiring sustained behavior.



Recording rules save calculated query results as reusable time series.

The lab records request rate, error rate, and p95 latency.



\### Aggregation and matching



sum by (job, instance) preserves the listed labels.

sum without (route, status) removes those labels and preserves others.



Binary operations match series by labels.

on selects the labels used for matching.

ignoring excludes specified labels from matching.



group\_left permits many left-side series to match one right-side series.

group\_right permits one left-side series to match many right-side series.

The one-side must be unique for the matching labels.



Logical and retains matching left-side series.

unless retains left-side series without a right-side match.



Our alerts match on job and instance to associate each result with its target.



\### How failures become hidden



Comparisons normally filter series rather than returning false as zero.

If the input metric is absent, a comparison can return no series.



Other traps include:

\- Unmatched labels removing results during arithmetic.

\- Aggregation hiding which instance failed.

\- Dividing by zero when there is no traffic.

\- Treating absent metrics as healthy.

\- Averaging only available samples while ignoring monitoring gaps.

\- Removing a target so its up series disappears.



Evidence: PROMQL-RESEARCH.md and the recording-rule screenshot.



\## 2. Alert engineering



An alert is inactive when its expression returns no matching series.

It is pending while a condition awaits its for duration.

It becomes firing when that duration is satisfied.



for delays firing until the condition persists.

keep\_firing\_for retains firing briefly after the condition clears.

Both can reduce flapping, but affect detection or recovery timing.



Labels identify alerts and support routing or grouping.

Annotations explain the condition and operator actions.



Alertmanager can:

\- Route alerts to appropriate receivers.

\- Group related alerts into fewer notifications.

\- Inhibit secondary notifications when another alert explains them.

\- Silence notifications during an agreed interval.



PromQL matching in our rules is different from Alertmanager inhibition.

The lab does not configure Alertmanager.



Severity should reflect impact and urgency.

A false positive raises an unnecessary alert.

A false negative misses a real problem.

Repeated unhelpful notifications cause alert fatigue.



The lab uses for: 0m to make experimental behavior easy to observe.

Its flapping test demonstrates repeated firing and clearing.

Longer timing settings require new tests before adoption.



Evidence: ALERT-DESIGN.md, eight unit-test scenarios,

and live failure screenshots.



\## 3. Grafana and investigation



Grafana queries a data source and displays results in panels.

It does not collect our Prometheus metrics itself.



Instant queries support current-status panels.

Range queries support graphs of changes over time.

The dashboard time range must include the incident being investigated.



Dashboard variables allow reusable filters such as job or instance.

This lab currently uses fixed job filters.



RED describes service behavior:

\- Rate: requests per second.

\- Errors: failed requests.

\- Duration: request latency.



USE describes resource behavior:

\- Utilization: how busy a resource is.

\- Saturation: queued or waiting work.

\- Errors: resource failures.



RED is useful for investigating user-facing service symptoms.

USE helps investigate underlying resource constraints.



The lab has RED panels and process/filesystem measurements.

It does not measure complete host utilization or resource saturation.

A fuller USE dashboard would add queue, throttling, or waiting metrics.



An SLI measures a chosen aspect of service quality.

A useful incident dashboard combines service symptoms,

availability, resources, and dependency behavior.



Evidence: dashboard.json, GRAFANA-DASHBOARD.md, and screenshots.



\## 4. SRE and incident response



Monitoring measures system behavior.

Reliability engineering defines acceptable behavior and improves

the system and response process to meet it.



\- SLI: the measured indicator.

\- SLO: the target for that indicator over a defined period.

\- SLA: an agreement that may specify consequences for missing commitments.

\- Error budget: the unsuccessful fraction allowed by an SLO.



The proposed lab SLOs are documented in SRE-RUNBOOK.md.

They are not achieved production commitments.



An incident requires impact assessment, mitigation, recovery,

communication, and follow-up.



Escalation brings in the appropriate owner or additional expertise.

A runbook gives repeatable investigation and recovery steps.

A postmortem records the timeline, causes, and improvements.



Root-cause analysis must use evidence.

A symptom or successful restart alone does not establish the cause.



MTTD measures time until detection.

MTTR measures recovery time; the chosen start and end points must be stated.



Evidence: SRE-RUNBOOK.md and deliberate failure/recovery experiments.



\## 5. Metrics, logs, and traces



Metrics describe numerical patterns over time.

Logs describe individual events and contextual details.

Traces describe the sequence and duration of work across operations or services.



Investigation proceeds from the alert and metric spike to:

1\. The affected instance and time window.

2\. Logs for that service and window.

3\. Routes, statuses, error codes, and request IDs.

4\. A distributed trace when tracing is available.



Our JSON logs include UTC timestamp, level, service, request\_id,

route, status, duration\_seconds, and error\_code.



The verified PowerShell filter isolates structured ERROR events.

The runbook also provides an explicit historical UTC-window filter.



A request ID supports log correlation.

It is not a distributed trace or proof of trace propagation.



The lab implements metrics and logs, but no tracing backend.

A future tracing implementation would propagate trace context,

create spans, and export them to a collector/backend.



Evidence: application-error-logs.json and the runbook's log filters.



\## References



\- https://prometheus.io/docs/introduction/overview/

\- https://prometheus.io/docs/concepts/metric\_types/

\- https://prometheus.io/docs/prometheus/latest/querying/functions/

\- https://prometheus.io/docs/prometheus/latest/querying/operators/

\- https://prometheus.io/docs/prometheus/latest/configuration/alerting\_rules/

\- https://prometheus.io/docs/alerting/latest/overview/

\- https://prometheus.github.io/client\_python/

\- https://grafana.com/docs/grafana/latest/

\- https://sre.google/workbook/implementing-slos/

\- https://sre.google/workbook/error-budget-policy/

