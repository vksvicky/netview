Feature: Network discovery populates devices and topology

  Scenario: Running discovery with mock SNMP returns devices and edges
    Given an empty database
    When discovery runs with mocked SNMP responses
    Then the devices endpoint returns discovered devices
    And the topology contains nodes


