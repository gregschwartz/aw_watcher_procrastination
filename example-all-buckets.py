#!/usr/bin/env python3

from aw_client import ActivityWatchClient
from datetime import datetime, timedelta

def get_all_events():
    client = ActivityWatchClient("test-client")
    
    # Get all buckets
    buckets = client.get_buckets()
    print(f"Found {len(buckets)} buckets")
    
    # Get events from last 5 minutes
    start_time = datetime.now() - timedelta(minutes=5)
    
    all_events = []
    for bucket_id in buckets:
        # skip afk and input buckets
        if "afk_" in bucket_id or "input_" in bucket_id:
            continue

        events = client.get_events(
            bucket_id=bucket_id,
            start=start_time,
            limit=100
        )
        # add bucket_id to each event
        for event in events:
            # remove aw-watcher- from bucket_id as well as the _Gregs16ersonal2
            event.bucket_id = bucket_id.replace("aw-watcher-", "").split("_")[0]

        all_events.extend(events)
        
        print(f"\nFound {len(events)} events from bucket: {bucket_id}")

    # Sort events by timestamp
    all_events.sort(key=lambda x: x.timestamp)

    # Print events in chronological order
    for event in all_events:
        print(f"{event.timestamp}, {event.bucket_id}: {event.data}")
    
    return all_events

if __name__ == "__main__":
    events = get_all_events()
    print(f"\nTotal events found: {len(events)}") 