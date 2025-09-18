"""
Contract test for POST /sql/execute endpoint
Testing SQL execution (read-only) according to API specification
"""
import pytest
from fastapi.testclient import TestClient


class TestSqlExecuteContract:
    """Contract tests for SQL execution endpoint"""

    def test_execute_select_query(self, client: TestClient):
        """Test executing a simple SELECT query"""
        response = client.post(
            "/api/v1/sql/execute",
            json={
                "query": "SELECT * FROM users LIMIT 10"
            }
        )

        assert response.status_code == 200

        # Verify response structure
        data = response.json()
        assert "columns" in data
        assert "rows" in data
        assert "row_count" in data
        assert "execution_time" in data

        # Verify field types
        assert isinstance(data["columns"], list)
        assert isinstance(data["rows"], list)
        assert isinstance(data["row_count"], int)
        assert isinstance(data["execution_time"], (int, float))

        # Verify execution time is reasonable
        assert data["execution_time"] >= 0

    def test_execute_query_with_custom_limit(self, client: TestClient):
        """Test executing query with custom limit"""
        response = client.post(
            "/api/v1/sql/execute",
            json={
                "query": "SELECT * FROM jobs",
                "limit": 100
            }
        )

        assert response.status_code == 200

        data = response.json()
        # Should respect the limit
        assert data["row_count"] <= 100
        assert len(data["rows"]) <= 100

    def test_execute_query_default_limit(self, client: TestClient):
        """Test that default limit of 1000 is applied"""
        response = client.post(
            "/api/v1/sql/execute",
            json={
                "query": "SELECT * FROM jobs"  # No limit specified
            }
        )

        assert response.status_code == 200

        data = response.json()
        # Should not exceed default limit of 1000
        assert data["row_count"] <= 1000
        assert len(data["rows"]) <= 1000

    def test_execute_query_max_limit(self, client: TestClient):
        """Test maximum limit of 10000"""
        response = client.post(
            "/api/v1/sql/execute",
            json={
                "query": "SELECT * FROM users",
                "limit": 10000  # Max allowed
            }
        )

        assert response.status_code == 200

        data = response.json()
        assert data["row_count"] <= 10000

    def test_execute_query_exceeds_max_limit(self, client: TestClient):
        """Test with limit exceeding maximum"""
        response = client.post(
            "/api/v1/sql/execute",
            json={
                "query": "SELECT * FROM users",
                "limit": 20000  # Exceeds max of 10000
            }
        )

        # Should either cap at 10000 or return validation error
        assert response.status_code in [200, 422]

        if response.status_code == 200:
            data = response.json()
            assert data["row_count"] <= 10000

    def test_execute_aggregate_query(self, client: TestClient):
        """Test executing aggregate query"""
        response = client.post(
            "/api/v1/sql/execute",
            json={
                "query": "SELECT COUNT(*) as total, AVG(min_salary) as avg_salary FROM jobs"
            }
        )

        assert response.status_code == 200

        data = response.json()
        assert "columns" in data
        assert "rows" in data

        # Aggregate query should return one row
        if len(data["rows"]) > 0:
            assert len(data["rows"]) == 1

    def test_execute_join_query(self, client: TestClient):
        """Test executing JOIN query"""
        response = client.post(
            "/api/v1/sql/execute",
            json={
                "query": """
                    SELECT u.user_id, u.name, s.total_score
                    FROM users u
                    JOIN scores s ON u.user_id = s.user_id
                    LIMIT 10
                """
            }
        )

        assert response.status_code == 200

        data = response.json()
        assert "columns" in data
        assert "rows" in data

    def test_execute_insert_query_forbidden(self, client: TestClient):
        """Test that INSERT queries are forbidden"""
        response = client.post(
            "/api/v1/sql/execute",
            json={
                "query": "INSERT INTO users (name) VALUES ('test')"
            }
        )

        assert response.status_code == 403  # Forbidden

    def test_execute_update_query_forbidden(self, client: TestClient):
        """Test that UPDATE queries are forbidden"""
        response = client.post(
            "/api/v1/sql/execute",
            json={
                "query": "UPDATE users SET name = 'test' WHERE user_id = 1"
            }
        )

        assert response.status_code == 403  # Forbidden

    def test_execute_delete_query_forbidden(self, client: TestClient):
        """Test that DELETE queries are forbidden"""
        response = client.post(
            "/api/v1/sql/execute",
            json={
                "query": "DELETE FROM users WHERE user_id = 1"
            }
        )

        assert response.status_code == 403  # Forbidden

    def test_execute_drop_query_forbidden(self, client: TestClient):
        """Test that DROP queries are forbidden"""
        response = client.post(
            "/api/v1/sql/execute",
            json={
                "query": "DROP TABLE users"
            }
        )

        assert response.status_code == 403  # Forbidden

    def test_execute_invalid_sql_syntax(self, client: TestClient):
        """Test with invalid SQL syntax"""
        response = client.post(
            "/api/v1/sql/execute",
            json={
                "query": "SELEC * FORM users"  # Typos
            }
        )

        assert response.status_code == 400  # Bad request

    def test_execute_missing_query(self, client: TestClient):
        """Test without query field"""
        response = client.post(
            "/api/v1/sql/execute",
            json={}
        )

        assert response.status_code == 422  # Validation error

    def test_execute_empty_query(self, client: TestClient):
        """Test with empty query string"""
        response = client.post(
            "/api/v1/sql/execute",
            json={
                "query": ""
            }
        )

        assert response.status_code in [400, 422]

    def test_execute_query_with_parameters(self, client: TestClient):
        """Test query with WHERE conditions"""
        response = client.post(
            "/api/v1/sql/execute",
            json={
                "query": "SELECT * FROM jobs WHERE min_salary > 1500 AND pref_cd = 13 LIMIT 20"
            }
        )

        assert response.status_code == 200

        data = response.json()
        assert "columns" in data
        assert "rows" in data

    def test_execute_query_response_structure(self, client: TestClient):
        """Test detailed response structure"""
        response = client.post(
            "/api/v1/sql/execute",
            json={
                "query": "SELECT job_id, application_name FROM jobs LIMIT 5"
            }
        )

        if response.status_code == 200:
            data = response.json()

            # Check columns match query
            assert "job_id" in data["columns"]
            assert "application_name" in data["columns"]

            # Check rows structure
            for row in data["rows"]:
                assert isinstance(row, list)
                # Row should have same number of values as columns
                assert len(row) == len(data["columns"])