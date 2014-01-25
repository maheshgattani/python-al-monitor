#
# Script to tail, process and monitor a w3c access log (apache access log in this case).
# Example line in access log:
# www.xyz.com - - [25/Jan/2014:10:17:47 -0700] "GET /server-status HTTP/1.0" 200 2790 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.12.14"
#
# The script generates an alert when the number of requests for last 2 minutes exceed a threshold.
# We compute it by using a rotating window for last 2 minutes refreshed every 10 seconds.
#
# Sample output:
# Traffic summary for last 10.0 seconds
# Section : www.xyz.com, hits = 1
# Traffic info according to response codes
# Code : 200, hits = 1
#
# Sample Alert Message:
# ALERT: High traffic generated an alert - hits = 2002, triggered at 2012-09-15 19:40:07
#
# Sample Resolved Alert Message:
# RESOLVED: High traffic generated an alert - hits = 2002, triggered at 2012-09-15 19:40:07
#
# Simple shell script to test the alert
# for i in {1..1000}; do curl localhost/test1/test2; done
#
# Author: Mahesh Gattani
#

import time, os, Queue
from optparse import OptionParser
from time import gmtime, strftime

SLEEP_INTERVAL = 10.0 # keep it such that 120 % SLEEP_INTERVAL is 0
MAX_SIZE = 120 / SLEEP_INTERVAL # we will keep a rotating window for last 2 minutes to cature the number of requests
TRAFFIC_MAX_THRESHOLD = 15.0 # if the number of requests exceed this number, we alert
HIGH_HIT_SECTION_THRESHOLD = 100 # only output the section in the summary if it has more than these number of hits

#
# Helper function to handle processing of a access log line
#
def handle_url(full_url, processed_data):
    if full_url in processed_data:
        processed_data[full_url] = processed_data[full_url] + 1
    else:
        processed_data[full_url] = 1

#
# Process a single entry in access log and update metadata around it.
#
def process_line(line, processed_data, response_codes, total_requests_per_loop):
    data = line.split(" ")

    # sanatizing data
    try:
        int(data[0])
        data.pop(0)
        data.pop(0)
        data.pop(1)
    except:
        # do nothing
        i = 0

    # process and update request info
    url = data[6]
    url_parts = url.split("/")
    url_parts.pop(0)
    if len(url_parts) > 1:
        section = data[6].split("/")
        section.pop()
        full_url = data[0] + "/".join(section)
        handle_url(full_url, processed_data)
    else:
        full_url = data[0]
        handle_url(full_url, processed_data)

    # process and update reponse code data 8
    response_code = data[8]
    if response_code in response_codes:
        response_codes[response_code] = response_codes[response_code] + 1
    else:
        response_codes[response_code] = 1

    # update total request count
    total_requests_per_loop = total_requests_per_loop + 1
    return total_requests_per_loop

#
# Update the request count to be used for alerting later
#
def update_request_count(total_requests, no_of_requests):
    if len(no_of_requests) < MAX_SIZE:
        no_of_requests.append(total_requests)
    else:
        no_of_requests.pop(0)
        no_of_requests.append(total_requests)

#
# Returns true if the system went in alert state
#
def format_print_and_manage_alert(processed_data, response_codes, no_of_requests, alert_state, alert):
    print "\nTraffic summary for last " + str(SLEEP_INTERVAL) + " seconds"
    if len(processed_data) > 0:
        for section in sorted(processed_data, key=processed_data.get, reverse=True):
            if int(processed_data[section]) > HIGH_HIT_SECTION_THRESHOLD:
                print "Section : " + section + ", hits = " + str(processed_data[section]) 
    else:
        print "No traffic for last " + str(SLEEP_INTERVAL) + " seconds"

    print "Traffic info according to response codes"
    if len(response_codes) > 0:
        for response_code in sorted(response_codes, key=response_codes.get, reverse=True):
            print "Code : " + response_code + ", hits = " + str(response_codes[response_code])
    else:
        print "No traffic for last " + str(SLEEP_INTERVAL) + " seconds"
    
    requests_len = len(no_of_requests)
    sum_requests = sum(no_of_requests)
    if alert_state != True:
        # alert
        if sum_requests > TRAFFIC_MAX_THRESHOLD:
            alert = "High traffic generated an alert - hits = " + str(sum_requests) + ", triggered at " + strftime("%Y-%m-%d %H:%M:%S", gmtime())
            print "ALERT: " + alert
            return (True, alert)
    else:
        # resolve alert
        if sum_requests < TRAFFIC_MAX_THRESHOLD:
            print "RESOLVED: " + alert
            return (False, "")

    return (alert_state, alert)

def main():
    p = OptionParser("Usage: tail.py file")
    (options, args) = p.parse_args()
    if len(args) < 1:
        p.error("must specify a file to watch")

    # Reach the end of the file
    file = open(args[0], 'r')
    file.seek(os.fstat(file.fileno()).st_size)

    queue = Queue.Queue()
    processed_data = {}
    response_codes = {}
    no_of_requests = []
    total_requests_per_loop = 0
    alert_state = False
    alert = ""
    first_run = True

    # Now tail the file with sleeps of SLEEP_INTERVAL durations
    while 1:
        where = file.tell()
        line = file.readline()
        if not line:
            if first_run:
                first_run = False
            else:
                update_request_count(total_requests_per_loop, no_of_requests)
                (alert_state, alert) = format_print_and_manage_alert(processed_data, response_codes, no_of_requests, alert_state, alert)
                processed_data = {}
                response_codes = {}
                total_requests_per_loop = 0

            time.sleep(SLEEP_INTERVAL)
            file.seek(where)
        else:
            total_requests_per_loop = process_line(line, processed_data, response_codes, total_requests_per_loop)

if __name__ == '__main__':
    main()
