"""
Contract test for POST /jobs/import endpoint
Testing CSV import functionality according to API specification
"""
import pytest
from fastapi.testclient import TestClient
import io
import csv


class TestJobsImportContract:
    """Contract tests for jobs CSV import endpoint"""

    def create_csv_content(self, rows):
        """Helper to create CSV content"""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerows(rows)
        return output.getvalue()

    def test_import_valid_csv(self, client: TestClient):
        """Test importing valid CSV file"""
        csv_content = self.create_csv_content([
            ["job_id", "endcl_cd", "application_name", "min_salary", "max_salary", "fee", "pref_cd", "city_cd"],
            ["1", "END001", "コンビニスタッフ", "1000", "1200", "10", "13", "101"],
            ["2", "END002", "飲食店ホール", "1100", "1300", "15", "14", "201"]
        ])

        files = {
            "file": ("jobs.csv", csv_content, "text/csv")
        }

        response = client.post(
            "/api/v1/jobs/import",
            files=files
        )

        assert response.status_code == 200

        # Check response structure
        data = response.json()
        assert "imported" in data
        assert "skipped" in data
        assert "errors" in data

        # Verify field types
        assert isinstance(data["imported"], int)
        assert isinstance(data["skipped"], int)
        assert isinstance(data["errors"], list)

    def test_import_with_validation_only(self, client: TestClient):
        """Test CSV validation without actual import"""
        csv_content = self.create_csv_content([
            ["job_id", "endcl_cd", "application_name", "min_salary", "max_salary", "fee", "pref_cd", "city_cd"],
            ["1", "END001", "コンビニスタッフ", "1000", "1200", "10", "13", "101"]
        ])

        files = {
            "file": ("jobs.csv", csv_content, "text/csv")
        }

        response = client.post(
            "/api/v1/jobs/import",
            files=files,
            data={"validate_only": "true"}
        )

        assert response.status_code == 200

        data = response.json()
        # When validate_only, no actual import should happen
        assert "imported" in data
        assert "skipped" in data
        assert "errors" in data

    def test_import_csv_with_errors(self, client: TestClient):
        """Test importing CSV with invalid rows"""
        csv_content = self.create_csv_content([
            ["job_id", "endcl_cd", "application_name", "min_salary", "max_salary", "fee", "pref_cd", "city_cd"],
            ["1", "END001", "Valid Job", "1000", "1200", "10", "13", "101"],
            ["invalid", "END002", "Invalid Job", "not_number", "1300", "15", "14", "201"],  # Invalid row
            ["3", "END003", "Another Valid", "1100", "1400", "20", "15", "301"]
        ])

        files = {
            "file": ("jobs.csv", csv_content, "text/csv")
        }

        response = client.post(
            "/api/v1/jobs/import",
            files=files
        )

        assert response.status_code == 200

        data = response.json()
        assert data["errors"] is not None
        assert len(data["errors"]) > 0

        # Check error structure
        for error in data["errors"]:
            assert "row" in error
            assert "message" in error
            assert isinstance(error["row"], int)
            assert isinstance(error["message"], str)

    def test_import_empty_csv(self, client: TestClient):
        """Test importing empty CSV file"""
        csv_content = self.create_csv_content([
            ["job_id", "endcl_cd", "application_name", "min_salary", "max_salary", "fee", "pref_cd", "city_cd"]
        ])

        files = {
            "file": ("jobs.csv", csv_content, "text/csv")
        }

        response = client.post(
            "/api/v1/jobs/import",
            files=files
        )

        assert response.status_code == 200

        data = response.json()
        assert data["imported"] == 0
        assert data["skipped"] == 0

    def test_import_invalid_csv_format(self, client: TestClient):
        """Test importing invalid CSV format"""
        files = {
            "file": ("jobs.txt", "This is not a CSV", "text/plain")
        }

        response = client.post(
            "/api/v1/jobs/import",
            files=files
        )

        assert response.status_code == 400  # Bad request

    def test_import_missing_file(self, client: TestClient):
        """Test import endpoint without file"""
        response = client.post("/api/v1/jobs/import")

        assert response.status_code == 422  # Validation error

    def test_import_large_csv(self, client: TestClient):
        """Test importing large CSV file"""
        rows = [["job_id", "endcl_cd", "application_name", "min_salary", "max_salary", "fee", "pref_cd", "city_cd"]]

        # Create 1000 rows
        for i in range(1, 1001):
            rows.append([
                str(i),
                f"END{i:04d}",
                f"求人{i}",
                "1000",
                "2000",
                "10",
                str((i % 47) + 1),  # Prefecture 1-47
                str((i % 100) + 1)
            ])

        csv_content = self.create_csv_content(rows)
        files = {
            "file": ("large_jobs.csv", csv_content, "text/csv")
        }

        response = client.post(
            "/api/v1/jobs/import",
            files=files
        )

        assert response.status_code == 200

        data = response.json()
        assert data["imported"] + data["skipped"] == 1000