from pathlib import Path

from drdroid_debug_toolkit import DroidSDK


CREDENTIALS_FILE_PATH = str(Path(__file__).parent / "credentials.yaml")

# MySQL high load check using SDK SQL task: show full processlist and ignore Sleep
MYSQL_PROCESSLIST_QUERY = "show full processlist;"


def execute_sql_query(credentials_file_path: str, query: str) -> None:
    sdk = DroidSDK(credentials_file_path)
    result = sdk.sql_database_connection.execute_sql_query(
        query=query,
        timeout=120,
    )
    print("Result:")
    print(result)


if __name__ == "__main__":
    execute_sql_query(
        credentials_file_path=CREDENTIALS_FILE_PATH,
        query=MYSQL_PROCESSLIST_QUERY,
    )
