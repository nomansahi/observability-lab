\## Initial lab evidence



\### Successful scrape

The Targets page shows the Prometheus target as UP.



!\[Prometheus target UP](../evidence/prometheus-target-up.png)



\### Request rate

This query shows requests per second to Prometheus's metrics endpoint:



&#x20;   sum by (job) (rate(promhttp\_metric\_handler\_requests\_total{job="prometheus"}\[2m]))



!\[Request rate](../evidence/prometheus-request-rate.png)



\### Missing series

This query returns 1 because the job is not configured:



&#x20;   absent(up{job="not-configured"})



This demonstrates missing data, not a real target failure.



!\[Missing series](../evidence/prometheus-missing-series.png)







\## Queries and results



\### 1. Scrape status



&#x20;   up{job="prometheus"}



Shows whether the latest scrape succeeded.

Observed result: 1, meaning the scrape succeeded.



\### 2. Scrape duration



&#x20;   scrape\_duration\_seconds{job="prometheus"}



Shows how long the latest scrape took, in seconds.

Observed result: 0.011153458 seconds, about 11.15 milliseconds.



\### 3. Samples collected



&#x20;   scrape\_samples\_scraped{job="prometheus"}



Shows how many metric samples were collected in the latest scrape.

Observed result: 883 samples.











\### 4. Successful request count



&#x20;   promhttp\_metric\_handler\_requests\_total{job="prometheus",code="200"}



Counts successful requests to Prometheus's metrics endpoint.

Observed result: 35. This counter increases and can reset after a restart.



\### 5. Successful requests per second



&#x20;   rate(promhttp\_metric\_handler\_requests\_total{job="prometheus",code="200"}\[2m])



Shows the average successful request rate over two minutes.

Observed result: about 0.0687 requests per second.



\### 6. Successful requests over two minutes



&#x20;   increase(promhttp\_metric\_handler\_requests\_total{job="prometheus",code="200"}\[2m])



Estimates how many successful requests occurred in two minutes.

Observed result: about 8.33. Extrapolation can produce fractional results.



\### 7. HTTP error percentage



&#x20;   100 \* sum by (job) (rate(promhttp\_metric\_handler\_requests\_total{job="prometheus",code=\~"5.."}\[2m])) / sum by (job) (rate(promhttp\_metric\_handler\_requests\_total{job="prometheus"}\[2m]))



Shows the percentage of metrics-endpoint requests returning a 5xx error.

Observed result: 0%.

If the total request rate is zero, this ratio is undefined.



\### 8. Process memory



&#x20;   process\_resident\_memory\_bytes{job="prometheus"} / 1024 / 1024



Shows the Prometheus process's resident memory in MiB.

Observed result: about 100.07 MiB.

This is a gauge, so its value can rise or fall.



\### 9. Process CPU usage



&#x20;   rate(process\_cpu\_seconds\_total{job="prometheus"}\[2m]) \* 100



Shows CPU usage as a percentage of one CPU core, averaged over two minutes.

Observed result: about 0.91%.

This measures the Prometheus process, not the whole computer.



\### 10. Missing-series detection



&#x20;   absent(up{job="not-configured"})



Returns 1 when no series matches this selector.

Observed result: 1 because this job was never configured.

This demonstrates absence; it does not prove a target failed.





\## Practice application queries



The practice application temporarily substitutes for the Vote application.

Run these queries in Prometheus or Grafana.



\### 1. Application metrics scrape status



```promql

up{job="practice\_app"}

```



1 means the metrics scrape succeeded; 0 means it failed.

This alone does not prove that application features work.



\### 2. HTTP availability check



```promql

probe\_success{job="site\_probe",instance="http://app:8000/health"}

```



1 means the HTTP health check succeeded; 0 means it failed.

An absent result means the check result is unavailable.



\### 3. Request rate



```promql

sum(rate(app\_http\_requests\_total{job="practice\_app"}\[5m]))

```



Application requests per second, averaged over five minutes.



\### 4. Server-error percentage



```promql

100 \*

sum(rate(app\_http\_requests\_total{job="practice\_app",status=\~"5.."}\[5m]))

/

sum(rate(app\_http\_requests\_total{job="practice\_app"}\[5m]))

```



Percentage of observed requests returning HTTP 500–599.

Zero traffic makes the ratio undefined.

A missing error series can also produce no result.



Observed during a deliberate experiment: approximately 35.9%.

This was a short-window result, not a monthly SLO measurement.



\### 5. Estimated p95 request latency



```promql

histogram\_quantile(

&#x20; 0.95,

&#x20; sum by (le) (

&#x20;   rate(app\_http\_request\_duration\_seconds\_bucket{job="practice\_app"}\[5m])

&#x20; )

)

```



Estimated duration below which 95% of requests fall, in seconds.



The le label is the histogram bucket's upper boundary.

Bucket spacing affects precision.



After slow requests, the observed estimate was 1.95 seconds.

The requests took just over one second and fell in the 1–2 second bucket.



\### 6. Instances with failed HTTP checks



```promql

(probe\_success{job="site\_probe"} == 0)

and on (job, instance)

(up{job="site\_probe"} == 1)

```



Returns targets whose probe failed while collection succeeded.



\### 7. Failed metrics scrapes



```promql

up{job=\~"practice\_app|site\_probe"} == 0

```



Returns configured targets that Prometheus cannot scrape.

It does not detect targets removed from configuration.



\### 8. Missing probe result during a successful scrape



```promql

(up{job="site\_probe"} == 1)

unless on (job, instance)

probe\_success{job="site\_probe"}

```



Returns successfully scraped targets without a probe\_success series.

This distinguishes missing results from scrape failures.



\### 9. Application process CPU



```promql

100 \* rate(process\_cpu\_seconds\_total{job="practice\_app"}\[5m])

```



CPU usage as a percentage of one core.

100% means one core; multiple cores can produce values above 100%.



\### 10. Application process memory



```promql

process\_resident\_memory\_bytes{job="practice\_app"}

```



Resident memory used by the process, in bytes.

This is not total host or container memory usage.



\### 11. Filesystem used percentage



```promql

100 \* (

&#x20; 1 -

&#x20; app\_filesystem\_free\_bytes{job="practice\_app"}

&#x20; /

&#x20; app\_filesystem\_total\_bytes{job="practice\_app"}

)

```



Used space on the filesystem visible at /app inside the container.

This is not the Windows drive or space used only by the application.



\### 12. Database connection health



```promql

app\_db\_connection\_success{job="practice\_app"}

```



Whether the latest SQLite connection and SELECT 1 succeeded.

Individual SQL queries can fail while this remains 1.



\### 13. Database query error rate



```promql

sum(rate(app\_db\_queries\_total{job="practice\_app",result="error"}\[5m]))

```



Failed application database operations per second.

Background connection checks are excluded.



\### 14. Database p95 operation latency



```promql

histogram\_quantile(

&#x20; 0.95,

&#x20; sum by (le) (

&#x20;   rate(app\_db\_query\_duration\_seconds\_bucket{job="practice\_app"}\[5m])

&#x20; )

)

```



Estimated database operation p95, including connection setup

and failed operations.



\### 15. Missing application scrape-status series



```promql

absent(up{job="practice\_app",instance="app:8000"})

```



Returns 1 when the specified series is absent.

A present up=0 series does not trigger absent().



This check assumes app:8000 is an expected target.

Larger systems need an inventory of expected targets.



\### 16. Fraction of requests completed within 500 ms



```promql

sum(rate(app\_http\_request\_duration\_seconds\_bucket{job="practice\_app",le="0.5"}\[5m]))

/

sum(rate(app\_http\_request\_duration\_seconds\_count{job="practice\_app"}\[5m]))

```



Fraction of measured requests meeting the proposed latency threshold.

Multiply by 100 for a percentage.



This is a five-minute diagnostic query, not proof of meeting

the proposed 30-day SLO. With no traffic, it is undefined.



\### 17. Recorded request rate



```promql

instance:app\_http\_requests:rate5m

```



The request-rate result stored by a recording rule.

An observed result after generated traffic was approximately

0.118 requests per second.



\## Measurement lessons



Counters record cumulative events and reset when the process restarts.

rate() measures changes between samples and handles counter resets.



If a counter first appears after a traffic burst, Prometheus may

first observe its already-increased value. Those earlier events

are not necessarily visible as an increase between scraped samples.



Instant queries show the value at one evaluation time.

Range queries repeat evaluation across a time interval.



Missing data is different from zero.

A dashboard showing no errors must be checked alongside traffic,

scrape status, and metric presence.



The application excludes /metrics and /health from request metrics.

Unknown routes share the unmatched label to limit cardinality.

Request IDs are kept in logs rather than metric labels.







