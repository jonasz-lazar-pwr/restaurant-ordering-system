# tests/run_all_tests.py

"""
Main test runner for all microservices.

This script sequentially runs the individual test runners for each microservice
(e.g., auth-service, notification-service). It delegates the execution to each
sub-runner script defined in the `services` list.

Usage:
    $ python run_all_tests.py
"""

import subprocess

# List of relative paths to individual microservice test runners
services = [
    "auth-service/run_auth_tests.py",
    "order-service/run_order_tests.py",
    # "staff-service/run_staff_tests.py",
    # "payment-service/run_payment_tests.py",
    # "notification-service/run_notification_tests.py",
]

if __name__ == "__main__":
    for service_runner in services:
        print(f"Running tests for: {service_runner}")
        subprocess.run(["python", service_runner])
