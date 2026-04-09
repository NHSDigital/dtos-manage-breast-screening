Feature: Participant record
  Details of the participant can be viewed from an upcoming appointment.

  Scenario: Viewing the participant record

    Given I am logged in as an administrative user
    And the participant has an upcoming appointment
    And I am viewing the upcoming appointment
    When I click on participant details
    Then I should be on the participant record page
    And I should see the participant record
    When I click on the back link
    Then I should be back on the appointment

  Scenario: Accessibility check

    Given I am logged in as an administrative user
    And the participant has an upcoming appointment
    And I am viewing the upcoming appointment
    Then the accessibility baseline is met
