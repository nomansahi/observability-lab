\# Alert Design



\## Purpose



These alerts distinguish a failed HTTP probe from a monitoring problem.



The original expression checked only:



&#x20;   probe\_success{job="site\_probe"} == 0



If the scrape fails and probe\_success is absent, this expression

returns no result. The alert can remain quiet despite a monitoring failure.



\## Alert behavior



| Condition | Alert |

| --- | --- |

| up=1, probe\_success=1 | None |

| up=1, probe\_success=0 | SiteProbeFailed |

| up=0, probe\_success absent | SiteProbeScrapeFailed |

| up=1, probe\_success absent | SiteProbeResultMissing |



\### SiteProbeFailed



The scrape succeeded, but the HTTP probe reported failure.



Check the target URL, HTTP response, DNS, TLS, connectivity,

and probe configuration. A failed probe does not prove that

the application process has stopped.



\### SiteProbeScrapeFailed



Prometheus could not scrape the probe endpoint.



Check the Prometheus target error, exporter, scrape address,

and connectivity. The application's health is unknown.



\### SiteProbeResultMissing



The scrape succeeded, but probe\_success was missing.



Check the probe endpoint, module settings, and metric filtering.

The application's health is unknown.



\## Matching targets



The rules use job and instance to match metrics for the same target.



The probe-failure rule requires up=1.

The missing-result rule also requires up=1.

This keeps both alerts quiet when the scrape-failure alert fires.



\## Test scenarios



The test suite contains eight independent scenarios:



1\. Healthy probe: all alerts stay quiet.

2\. HTTP probe failure: only SiteProbeFailed fires.

3\. Scrape failure: only SiteProbeScrapeFailed fires.

4\. Probe recovery: SiteProbeFailed fires, then clears.

5\. Scrape recovery: SiteProbeScrapeFailed fires, then clears.

6\. Probe result disappears: only SiteProbeResultMissing fires.

7\. Flapping: SiteProbeFailed fires, clears, and fires again.

8\. Multiple failures: each failing instance gets its own probe alert.



At each checked time, the tests specify which alerts should fire

and which must stay quiet.



The disappearing-result test uses stale to mark the old metric

as unavailable. The underscore means no sample is supplied.



\## Timing



All three rules currently use for: 0m.



An alert fires at the first rule evaluation where its condition

is true. The flapping test demonstrates how this can produce

repeated alert changes.



A longer for duration could reduce alerts from brief failures,

but it would also delay detection. Timing changes need separate tests.



\## Validation



Run from the project root:



&#x20;   docker compose run --rm --no-deps --entrypoint /bin/promtool -v "${PWD}:/lab:ro" -w /lab/tests prometheus test rules alert-tests.yml



The observed result was SUCCESS.



Evidence is saved in:



&#x20;   evidence/alert-test-output.txt



\## Limitations



These are unit tests using supplied metric samples.

They do not prove live scraping or notification delivery.



If the target disappears completely and up is also absent,

these three rules cannot detect it. That requires a separate

check against the expected targets.



A stopped Prometheus server also requires monitoring from

outside that server.

