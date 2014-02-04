pyhton-al-monitor
=================

Access log  monitoring and alerting based on it.

Script to tail, process and monitor a w3c access log (apache access log in this case).

Example line in access log:
www.xyz.com - - [25/Jan/2014:10:17:47 -0700] "GET /server-status HTTP/1.0" 200 2790 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.12.14"

The script generates an alert when the number of requests for last 2 minutes exceed a threshold.
We compute it by using a rotating window for last 2 minutes refreshed every 10 seconds.

Sample output:
Traffic summary for last 10.0 seconds
Section : www.xyz.com, hits = 1
Traffic info according to response codes
Code : 200, hits = 1

Sample Alert Message:
ALERT: High traffic generated an alert - hits = 2002, triggered at 2012-09-15 19:40:07

Sample Resolved Alert Message:
RESOLVED: High traffic generated an alert - hits = 2002, triggered at 2012-09-15 19:40:07

Simple shell script to test the alert
`for i in {1..1000}; do curl localhost/test1/test2; done`
