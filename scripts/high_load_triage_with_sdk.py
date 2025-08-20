from pathlib import Path
from typing import List
from drdroid_debug_toolkit import DroidSDK

CREDENTIALS_FILE_PATH = str(Path(__file__).parent / "credentials.yaml")
# Core commands used to triage high load on a Linux server
BASH_COMMANDS_FOR_HIGH_LOAD_TRIAGE: List[str] = [
    "w",
    "ps aux",
    "df -h",
]
def execute_bash_commands_with_sdk(credentials_file_path: str, commands: List[str]) -> None:
    sdk = DroidSDK(credentials_file_path)
    for command in commands:
        print(f"\n--- Executing: {command} ---")
        result = sdk.bash.execute_command(command=command)
        print("Result:")
        print(result)

if __name__ == "__main__":
    execute_bash_commands_with_sdk(
        credentials_file_path=CREDENTIALS_FILE_PATH,
        commands=BASH_COMMANDS_FOR_HIGH_LOAD_TRIAGE,
    )
