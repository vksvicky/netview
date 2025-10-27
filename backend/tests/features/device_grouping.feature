Feature: Device Grouping
  As a network administrator
  I want to group devices by different criteria
  So that I can organize and manage my network devices more effectively

  Background:
    Given an empty database with device grouping enabled

  Scenario: Group devices by vendor
    Given the following devices exist:
      | hostname | mgmt_ip     | vendor | model        | status |
      | Router1  | 192.168.1.1 | Cisco  | ISR4331      | up     |
      | Switch1  | 192.168.1.2 | Cisco  | Catalyst2960 | up     |
      | Server1  | 192.168.1.3 | HP     | ProLiant     | up     |
      | Unknown1 | 192.168.1.4 |        |              | down   |
    When I request devices grouped by vendor
    Then I should see the following groups:
      | group_name | device_count |
      | Cisco      | 2            |
      | HP         | 1            |
      | Unknown    | 1            |
    And each group should contain the correct devices

  Scenario: Group devices by status
    Given the following devices exist:
      | hostname | mgmt_ip     | vendor | model        | status |
      | Router1  | 192.168.1.1 | Cisco  | ISR4331      | up     |
      | Switch1  | 192.168.1.2 | Cisco  | Catalyst2960 | down   |
      | Server1  | 192.168.1.3 | HP     | ProLiant     | up     |
      | Unknown1 | 192.168.1.4 | Dell   | PowerEdge    | unknown|
    When I request devices grouped by status
    Then I should see the following groups:
      | group_name | device_count |
      | up         | 2            |
      | down       | 1            |
      | unknown    | 1            |

  Scenario: Group devices by connection type
    Given the following devices exist:
      | hostname | mgmt_ip     | vendor | model        | status | connection_type |
      | Router1  | 192.168.1.1 | Cisco  | ISR4331      | up     | SNMP            |
      | Switch1  | 192.168.1.2 | Cisco  | Catalyst2960 | up     | SNMP            |
      | Server1  | 192.168.1.3 | HP     | ProLiant     | up     | SSH             |
      | Unknown1 | 192.168.1.4 | Dell   | PowerEdge    | up     |                 |
    When I request devices grouped by connection type
    Then I should see the following groups:
      | group_name | device_count |
      | SNMP       | 2            |
      | SSH        | 1            |
      | Unknown    | 1            |

  Scenario: Group devices by device type
    Given the following devices exist:
      | hostname | mgmt_ip     | vendor | model        | status | roles     |
      | Router1  | 192.168.1.1 | Cisco  | ISR4331      | up     | router    |
      | Switch1  | 192.168.1.2 | Cisco  | Catalyst2960 | up     | switch    |
      | Server1  | 192.168.1.3 | HP     | ProLiant     | up     | server    |
      | Gateway1 | 192.168.1.4 | Dell   | PowerEdge    | up     | gateway   |
      | Cisco1   | 192.168.1.5 | Cisco  | ASA          | up     |           |
      | HP1      | 192.168.1.6 | HP     | Aruba        | up     |           |
      | Dell1    | 192.168.1.7 | Dell   | PowerEdge    | up     |           |
      | Other1   | 192.168.1.8 | Other  | Unknown      | up     |           |
    When I request devices grouped by device type
    Then I should see the following groups:
      | group_name     | device_count |
      | Router/Gateway | 2            |
      | Switch         | 1            |
      | Server         | 1            |
      | Cisco Device   | 1            |
      | HP Device      | 1            |
      | Dell Device    | 1            |
      | Other Device   | 1            |

  Scenario: Get grouping statistics
    Given the following devices exist:
      | hostname | mgmt_ip     | vendor | model        | status | connection_type | roles  |
      | Router1  | 192.168.1.1 | Cisco  | ISR4331      | up     | SNMP            | router |
      | Switch1  | 192.168.1.2 | Cisco  | Catalyst2960 | down   | SNMP            | switch |
      | Server1  | 192.168.1.3 | HP     | ProLiant     | up     | SSH             | server |
      | Unknown1 | 192.168.1.4 |        |              | unknown|                 |        |
    When I request grouping statistics
    Then I should see vendor statistics:
      | vendor  | count |
      | Cisco   | 2     |
      | HP      | 1     |
      | Unknown | 1     |
    And I should see status statistics:
      | status  | count |
      | up      | 2     |
      | down    | 1     |
      | unknown | 1     |
    And I should see connection type statistics:
      | connection_type | count |
      | SNMP            | 2     |
      | SSH             | 1     |
      | Unknown         | 1     |
    And I should see device type statistics:
      | device_type     | count |
      | Router/Gateway  | 1     |
      | Switch          | 1     |
      | Server          | 1     |
      | Other Device    | 1     |

  Scenario: Handle empty database
    Given no devices exist
    When I request devices grouped by vendor
    Then I should receive an empty response
    When I request grouping statistics
    Then I should receive empty statistics for all grouping types

  Scenario: Handle devices with null values
    Given the following devices exist:
      | hostname | mgmt_ip     | vendor | model | status | connection_type | roles |
      | Device1  | 192.168.1.1 |        |       |        |                 |       |
      | Device2  | 192.168.1.2 | Cisco  | ISR   | up     | SNMP            |       |
    When I request devices grouped by vendor
    Then I should see the following groups:
      | group_name | device_count |
      | Unknown    | 1            |
      | Cisco      | 1            |

  Scenario: Sort grouped devices
    Given the following devices exist:
      | hostname | mgmt_ip     | vendor | model | status |
      | Z-Device | 192.168.1.1 | Cisco  | ISR   | up     |
      | A-Device | 192.168.1.2 | Cisco  | ISR   | up     |
      | M-Device | 192.168.1.3 | Cisco  | ISR   | up     |
    When I request devices grouped by vendor
    Then the Cisco group should contain devices in alphabetical order:
      | hostname |
      | A-Device |
      | M-Device |
      | Z-Device |

  Scenario: Invalid grouping criteria
    Given the following devices exist:
      | hostname | mgmt_ip     | vendor | model | status |
      | Device1  | 192.168.1.1 | Cisco  | ISR   | up     |
    When I request devices grouped by invalid criteria
    Then all devices should be grouped under "Unknown"
