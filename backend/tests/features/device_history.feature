Feature: Device History Tracking

  Scenario: Track device online events during discovery
    Given an empty database
    When discovery finds a new device "test-device-1" with IP "192.168.1.100"
    Then device history should contain an "online" event for "test-device-1"
    And the event should have new_ip "192.168.1.100"
    And the event should have new_status "up"

  Scenario: Track device offline events when device disappears
    Given a device "test-device-1" exists in the database
    When discovery runs and does not find "test-device-1"
    Then device history should contain an "offline" event for "test-device-1"
    And the event should have previous_status "up"

  Scenario: Track device IP changes
    Given a device "test-device-1" exists with IP "192.168.1.100"
    When discovery finds "test-device-1" with new IP "192.168.1.101"
    Then device history should contain an "ip_change" event for "test-device-1"
    And the event should have previous_ip "192.168.1.100"
    And the event should have new_ip "192.168.1.101"

  Scenario: Track device status changes
    Given a device "test-device-1" exists with status "up"
    When discovery finds "test-device-1" with status "down"
    Then device history should contain a "status_change" event for "test-device-1"
    And the event should have previous_status "up"
    And the event should have new_status "down"

  Scenario: Calculate session duration for offline events
    Given a device "test-device-1" has an active session started 2 hours ago
    When the device goes offline
    Then device history should contain an "offline" event for "test-device-1"
    And the event should have duration_seconds approximately 7200

  Scenario: Retrieve device history via API
    Given device history contains events for "test-device-1"
    When I request device history for "test-device-1"
    Then the API should return the device history events
    And events should be ordered by timestamp descending

  Scenario: Get device session statistics
    Given device history contains multiple sessions for "test-device-1"
    When I request session statistics for "test-device-1"
    Then the API should return total sessions count
    And the API should return total online time
    And the API should return average session duration

  Scenario: Filter device history by event type
    Given device history contains various event types for "test-device-1"
    When I request device history filtered by event_type "online"
    Then the API should return only "online" events

  Scenario: Get recent events across all devices
    Given device history contains recent events for multiple devices
    When I request recent events for the last 24 hours
    Then the API should return events from the last 24 hours
    And events should be ordered by timestamp descending

  Scenario: Get history summary statistics
    Given device history contains events for multiple devices
    When I request history summary for the last 7 days
    Then the API should return total events count
    And the API should return unique devices count
    And the API should return events by type breakdown
    And the API should return most active devices list
