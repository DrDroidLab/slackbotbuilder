from pathlib import Path
from typing import List

from drdroid_debug_toolkit import DroidSDK


CREDENTIALS_FILE_PATH = str(Path(__file__).parent / "credentials.yaml")

DISK_IO_TRIAGE_COMMANDS: List[str] = [
    "iostat -dx 1 5",
    "iotop -o",
]


def execute_commands(credentials_file_path: str, commands: List[str]) -> None:
    sdk = DroidSDK(credentials_file_path)
    for command in commands:
        print(f"\n--- Executing: {command} ---")
        result = sdk.bash.execute_command(command=command)
        print("Result:")
        print(result)


if __name__ == "__main__":
    execute_commands(
        credentials_file_path=CREDENTIALS_FILE_PATH,
        commands=DISK_IO_TRIAGE_COMMANDS,
    )
