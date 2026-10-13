\# Failure Scenarios



These experiments use Prometheus's HTTP health endpoint as a lab

target. They do not test the Vote application.



\## 1. Scrape failure



Stop Blackbox Exporter:



&#x20;   docker compose stop blackbox



Expected:

\- up=0

\- probe\_success absent

\- Only SiteProbeScrapeFailed fires.



Restore:



&#x20;   docker compose start blackbox



Evidence: ../evidence/scrape-failure-alert.png



\## 2. HTTP probe failure



In prometheus/prometheus.yml, change the probe target to:



&#x20;   http://prometheus:9090/deliberately-missing-page



Apply:



&#x20;   docker compose restart prometheus



Expected:

\- up=1

\- probe\_success=0

\- Only SiteProbeFailed fires for the changed target.



Restore the target to:



&#x20;   http://prometheus:9090/-/healthy



Restart Prometheus again.



Evidence: ../evidence/http-probe-failure-alert.png



\## 3. Missing probe result



Add this under the site\_probe job:



&#x20;   metric\_relabel\_configs:

&#x20;     - source\_labels: \[\_\_name\_\_]

&#x20;       regex: probe\_success

&#x20;       action: drop



Apply:



&#x20;   docker compose restart prometheus



Expected:

\- up=1

\- probe\_success absent

\- Only SiteProbeResultMissing fires.



Restore by removing the metric\_relabel\_configs section

and restarting Prometheus.



Evidence: ../evidence/probe-result-missing-alert.png



\## Recovery checks



After each restoration:

\- up=1

\- probe\_success=1

\- All three alerts become inactive.



Scrapes and rule evaluations run every 15 seconds.

Allow time for both before checking results.



After a restart, older samples may remain visible temporarily.

Changing the target URL also changes the instance label.

Check the Targets page to confirm the currently configured target.

