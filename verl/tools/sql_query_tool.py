# Copyright 2025 Bytedance Ltd. and/or its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Example SQL query tool using BaseTool.

Usage:
    pip install sqlite3  # (stdlib, no install needed)

    # python code:
    from verl.tools.tool_registry import load_all_tools

    tools = load_all_tools(
        tool_config_path="configs/sql_tool.yaml",
        function_tool_path=None,
    )

YAML config:
    tools:
      - class_name: verl.tools.sql_query_tool.SQLQueryTool
        config:
          type: native
          db_path: "/path/to/database.db"
        tool_schema:
          type: function
          function:
            name: sql_query
            description: "Execute a SQL query against the database and return results."
            parameters:
              type: object
              properties:
                query:
                  type: string
                  description: "The SQL query to execute, e.g. SELECT * FROM users"
              required:
                - query
"""

import json
import sqlite3
from typing import Any

from verl.tools.base_tool import BaseTool
from verl.tools.schemas import OpenAIFunctionToolSchema, ToolResponse


class SQLQueryTool(BaseTool):
    """A simple SQL query tool that executes read-only SQL queries."""

    def __init__(self, config: dict, tool_schema: OpenAIFunctionToolSchema = None):
        # Use default schema if none provided
        if tool_schema is None:
            tool_schema = OpenAIFunctionToolSchema(
                type="function",
                function={
                    "name": "sql_query",
                    "description": "Execute a SQL query and return the results as a JSON list.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The SQL query to execute (SELECT only).",
                            },
                        },
                        "required": ["query"],
                    },
                },
            )
        super().__init__(config, tool_schema)
        self.db_path = config.get("db_path", ":memory:")
        self._connections: dict[str, sqlite3.Connection] = {}

    async def create(self, instance_id: str = None, **kwargs) -> tuple[str, ToolResponse]:
        """Open a database connection."""
        instance_id, _ = super().create(instance_id, **kwargs)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column-name access
        self._connections[instance_id] = conn
        return instance_id, ToolResponse(text=f"Connected to database: {self.db_path}")

    async def execute(
        self, instance_id: str, parameters: dict[str, Any], **kwargs
    ) -> tuple[ToolResponse, float, dict]:
        """Execute a read-only SQL query."""
        conn = self._connections.get(instance_id)
        if conn is None:
            return ToolResponse(text=f"Error: No active connection for instance '{instance_id}'."), 0.0, {}

        query = parameters.get("query", "")
        query_upper = query.strip().upper()

        # Safety: only allow SELECT queries
        if not query_upper.startswith("SELECT"):
            return ToolResponse(text="Error: Only SELECT queries are allowed."), 0.0, {}

        try:
            cursor = conn.execute(query)
            rows = [dict(row) for row in cursor.fetchall()]
            result = {
                "rows": rows,
                "row_count": len(rows),
                "columns": [desc[0] for desc in cursor.description] if cursor.description else [],
            }
            text = f"Query returned {len(rows)} row(s).\n{json.dumps(result, indent=2)}"
            return ToolResponse(text=text), 0.0, {}
        except Exception as e:
            return ToolResponse(text=f"SQL error: {e}"), 0.0, {}

    async def calc_reward(self, instance_id: str, **kwargs) -> float:
        """Return a simple reward based on query success (just an example)."""
        conn = self._connections.get(instance_id)
        return 1.0 if conn else 0.0

    async def release(self, instance_id: str, **kwargs) -> None:
        """Close the database connection."""
        conn = self._connections.pop(instance_id, None)
        if conn:
            conn.close()


