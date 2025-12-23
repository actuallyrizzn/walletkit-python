"""Pytest configuration for integration tests."""
import os
import pytest

# Mark all tests in this directory as integration tests
pytestmark = pytest.mark.integration


def pytest_configure(config):
    """Configure pytest for integration tests."""
    # Check if PROJECT_ID is set
    project_id = os.getenv("WALLETCONNECT_PROJECT_ID")
    if not project_id or project_id == "test-project-id":
        # Mark integration tests to skip if no real PROJECT_ID
        config.option.markexpr = "not integration or integration_skip"


@pytest.fixture(scope="session")
def project_id():
    """Get WalletConnect Project ID from environment."""
    project_id = os.getenv("WALLETCONNECT_PROJECT_ID", "test-project-id")
    if project_id == "test-project-id":
        pytest.skip("WALLETCONNECT_PROJECT_ID not set - skipping integration tests")
    return project_id

