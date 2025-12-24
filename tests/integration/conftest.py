"""Pytest configuration for integration tests."""
import os
import pytest

# Mark all tests in this directory as integration tests
pytestmark = pytest.mark.integration


def pytest_configure(config):
    """Configure pytest for integration tests.

    Note: We intentionally do NOT rewrite pytest's mark expression here.
    Integration tests are skipped via the `project_id` fixture instead, so that
    running a test explicitly yields a clear SKIPPED reason (not "deselected").
    """
    return


@pytest.fixture(scope="session")
def project_id():
    """Get WalletConnect Project ID from environment."""
    project_id = os.getenv("WALLETCONNECT_PROJECT_ID", "test-project-id")
    if project_id in {"test-project-id", "a01e2f3b4c5d6e7f8a9b0c1d2e3f4a5b"}:
        pytest.skip(
            "WALLETCONNECT_PROJECT_ID not set (or still using the example placeholder) - "
            "skipping integration tests"
        )
    return project_id

