#!/bin/bash

# MESH Polling Test Scenarios
# This script demonstrates different testing approaches for the MESH polling system

set -e

echo "🔍 MESH Polling Test Scenarios"
echo "=============================="
echo ""

# Function to run tests with description
run_tests() {
    local description="$1"
    local command="$2"

    echo "📋 $description"
    echo "Command: $command"
    echo "---"
    eval "$command"
    echo ""
    echo "✅ Completed: $description"
    echo "=============================="
    echo ""
}

# Scenario 1: Unit Tests Only (Fast, No Dependencies)
echo "🚀 Scenario 1: Unit Tests Only"
echo "   - Fast execution"
echo "   - NO MESH client needed (all mocked)"
echo "   - NO Azure connection needed (all mocked)"
echo "   - Perfect for CI/CD"
echo ""
run_tests "Running unit tests (mocked)" \
    "poetry run pytest manage_breast_screening/notifications/tests/test_mesh_polling.py -v --tb=short"

# Scenario 2: Integration Tests (Real MESH Client)
echo "🔗 Scenario 2: Integration Tests"
echo "   - Real API validation"
echo "   - REQUIRES MESH client running"
echo "   - Tests actual connectivity"
echo "   - Gracefully skips if MESH unavailable"
echo ""
run_tests "Running integration tests (real MESH)" \
    "poetry run pytest manage_breast_screening/notifications/tests/test_mesh_integration.py -v --tb=short"

# Scenario 3: All Tests Together
echo "🎯 Scenario 3: Complete Test Suite"
echo "   - Unit + Integration tests"
echo "   - Comprehensive coverage"
echo "   - Best for local development"
echo ""
run_tests "Running complete test suite" \
    "poetry run pytest manage_breast_screening/notifications/tests/test_mesh_polling.py manage_breast_screening/notifications/tests/test_mesh_integration.py -v --tb=short"

# Scenario 4: CI/CD Pipeline (Unit Tests Only)
echo "🏭 Scenario 4: CI/CD Pipeline"
echo "   - Unit tests only"
echo "   - No external dependencies"
echo "   - Fast and reliable"
echo ""
run_tests "Running CI/CD pipeline tests" \
    "poetry run pytest manage_breast_screening/notifications/tests/test_mesh_polling.py -v --tb=short --junitxml=test-results.xml"

# Scenario 5: Selective Testing
echo "🎯 Scenario 5: Selective Testing"
echo "   - Specific test classes"
echo "   - Focused testing"
echo "   - Quick feedback"
echo ""
run_tests "Running specific test class" \
    "poetry run pytest manage_breast_screening/notifications/tests/test_mesh_polling.py::TestMeshPollingFunctions -v --tb=short"

echo "🎉 All test scenarios completed!"
echo ""
echo "📊 Summary:"
echo "   - Unit tests: Fast, reliable, no dependencies"
echo "   - Integration tests: Real validation, requires MESH client"
echo "   - Both approaches work together seamlessly"
echo ""
echo "💡 Usage Tips:"
echo "   - Use unit tests for CI/CD and quick development"
echo "   - Use integration tests for local validation"
echo "   - Integration tests gracefully skip when MESH unavailable"
