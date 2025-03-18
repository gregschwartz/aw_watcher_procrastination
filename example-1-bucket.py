#!/usr/bin/env python3

from time import sleep
from datetime import datetime, timezone

from aw_core.models import Event
from aw_client import ActivityWatchClient


# We'll run with testing=True so we don't mess up any production instance.
# Make sure you've started aw-server with the `--testing` flag as well.
client = ActivityWatchClient("test-client")



bucket_id = "aw-watcher-window_Gregs16ersonal2"

# Fetch last 10 events from bucket
# Should be two events in order of newest to oldest
# - "shutdown" event with a duration of 0
# - "heartbeat" event with a duration of 5*sleeptime
events = client.get_events(bucket_id=bucket_id, limit=10)
for event in events:
    print(event.timestamp, event.duration.total_seconds(), event.data["app"], event.data["title"])
