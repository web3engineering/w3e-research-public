"""ClickHouse database accessor module."""

import os
import clickhouse_connect
from typing import Optional, Any, List, Dict, Union
from .environment import load_environment


class ClickHouseAccessor:
    """ClickHouse database accessor that reads credentials from .env file."""

    def __init__(self, env_path: Optional[str] = None):
        """Initialize the ClickHouse accessor.

        Args:
            env_path: Path to .env file. Defaults to .env in repo root.
        """
        if env_path is None:
            # Get repo root (two levels up from core/)
            repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            env_path = os.path.join(repo_root, '.env')

        if not os.path.exists(env_path):
            raise FileNotFoundError(f".env file not found at {env_path}")

        env_vars = load_environment(env_path)

        self.host = env_vars.get('CLICKHOUSE_HOST')
        self.username = env_vars.get('CLICKHOUSE_USERNAME')
        self.password = env_vars.get('CLICKHOUSE_PASSWORD')
        self.port = int(env_vars.get('CLICKHOUSE_PORT', '8123'))

        if not all([self.host, self.username, self.password]):
            raise ValueError(
                "Missing required ClickHouse credentials in .env file. "
                "Required: CLICKHOUSE_HOST, CLICKHOUSE_USERNAME, CLICKHOUSE_PASSWORD"
            )

        self.client = None

    def connect(self):
        """Establish connection to ClickHouse database."""
        self.client = clickhouse_connect.get_client(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password
        )

    def disconnect(self):
        """Close connection to ClickHouse database."""
        if self.client:
            self.client.close()
            self.client = None

    def query(self, sql: str, parameters: Optional[Union[List[Any], Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """Execute a query and return results as list of dictionaries.

        Args:
            sql: SQL query string
            parameters: Optional query parameters (list or dict)

        Returns:
            List of dictionaries representing query results
        """
        if not self.client:
            self.connect()

        # Convert list parameters to dictionary format expected by clickhouse-connect
        if isinstance(parameters, list):
            # For list parameters, use positional parameter binding
            result = self.client.query(sql, parameters=parameters)
        else:
            # For dict parameters or None, pass as-is
            result = self.client.query(sql, parameters=parameters)

        # Convert result to list of dictionaries
        if result.result_rows:
            column_names = result.column_names
            return [dict(zip(column_names, row)) for row in result.result_rows]
        return []

    def query_df(self, sql: str, parameters: Optional[Union[List[Any], Dict[str, Any]]] = None):
        """Execute a query and return results as pandas DataFrame.

        Args:
            sql: SQL query string
            parameters: Optional query parameters (list or dict)

        Returns:
            pandas DataFrame with query results
        """
        if not self.client:
            self.connect()

        result = self.client.query_df(sql, parameters=parameters)
        return result

    def execute(self, sql: str, parameters: Optional[Dict[str, Any]] = None) -> None:
        """Execute a SQL statement without returning results.

        Args:
            sql: SQL statement
            parameters: Optional query parameters
        """
        if not self.client:
            self.connect()

        self.client.command(sql, parameters=parameters)

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


class HyperLiquidAccessor(ClickHouseAccessor):
    """ClickHouse accessor for HyperLiquid data using HL_* environment variables."""

    def __init__(self, env_path: Optional[str] = None):
        """Initialize the HyperLiquid ClickHouse accessor.

        Args:
            env_path: Path to .env file. Defaults to .env in repo root.
        """
        if env_path is None:
            # Get repo root (two levels up from core/)
            repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            env_path = os.path.join(repo_root, '.env')

        if not os.path.exists(env_path):
            raise FileNotFoundError(f".env file not found at {env_path}")

        env_vars = load_environment(env_path)

        # Parse URL format (host:port)
        url = env_vars.get('HL_CLICKHOUSE_URL')
        self.username = env_vars.get('HL_CLICKHOUSE_USER')
        self.password = env_vars.get('HL_CLICKHOUSE_PASSWORD')

        if not all([url, self.username, self.password]):
            raise ValueError(
                "Missing required HyperLiquid ClickHouse credentials in .env file. "
                "Required: HL_CLICKHOUSE_URL, HL_CLICKHOUSE_USER, HL_CLICKHOUSE_PASSWORD"
            )

        # Split URL into host and port
        if ':' in url:
            self.host, port_str = url.split(':', 1)
            self.port = int(port_str)
        else:
            self.host = url
            self.port = 8123

        self.client = None


class PolymarketAccessor(ClickHouseAccessor):
    """ClickHouse accessor for Polymarket data using POLY_* environment variables."""

    def __init__(self, env_path: Optional[str] = None):
        """Initialize the Polymarket ClickHouse accessor.

        Args:
            env_path: Path to .env file. Defaults to .env in repo root.
        """
        if env_path is None:
            # Get repo root (two levels up from core/)
            repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            env_path = os.path.join(repo_root, '.env')

        if not os.path.exists(env_path):
            raise FileNotFoundError(f".env file not found at {env_path}")

        env_vars = load_environment(env_path)

        # Parse URL format (host:port)
        url = env_vars.get('POLY_CLICKHOUSE_URL')
        self.username = env_vars.get('POLY_CLICKHOUSE_USER')
        self.password = env_vars.get('POLY_CLICKHOUSE_PASSWORD')

        if not all([url, self.username, self.password]):
            raise ValueError(
                "Missing required Polymarket ClickHouse credentials in .env file. "
                "Required: POLY_CLICKHOUSE_URL, POLY_CLICKHOUSE_USER, POLY_CLICKHOUSE_PASSWORD"
            )

        # Split URL into host and port
        if ':' in url:
            self.host, port_str = url.split(':', 1)
            self.port = int(port_str)
        else:
            self.host = url
            self.port = 8123

        self.client = None
