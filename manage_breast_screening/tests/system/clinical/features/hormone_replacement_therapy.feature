Feature: Hormone replacement therapy
  Add HRT information to the medical history

  Scenario: adding HRT information
    Given I am logged in as a clinical user
    And there is an appointment
    And i am on the record medical information page
    When i click add hormone replacement therapy
    Then i see the add hormone replacement therapy form

    When i click continue
    Then i see validation error for missing status

    When i select no
    And i click continue
    Then i am back on the medical information page
    And the message says hormone replacement therapy added
    And the hormone replacement therapy is displayed as not taken

    When i click change hormone replacement therapy
    Then i see the edit hormone replacement therapy form

    When i select yes
    And enter a duration
    And i click continue

    Then i am back on the medical information page
    And the message says hormone replacement therapy updated
    And the hormone replacement therapy is displayed as taken

  Scenario: accessibility check
    Given I am logged in as a clinical user
    And there is an appointment
    And i am on the add hormone replacement therapy page
    Then the accessibility baseline is met
