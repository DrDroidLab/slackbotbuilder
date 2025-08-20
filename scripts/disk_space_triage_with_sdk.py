from pathlib import Path
from typing import List

from drdroid_debug_toolkit import DroidSDK


CREDENTIALS_FILE_PATH = str(Path(__file__).parent / "credentials.yaml")

DISK_SPACE_TRIAGE_COMMANDS: List[str] = [
    "df -h",
    "sudo du -h / 2>/dev/null | sort -rh | head -15",
    "sudo find / -type f -exec du -h {} + 2>/dev/null | sort -rh | head -n 10",
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
        commands=DISK_SPACE_TRIAGE_COMMANDS,
    )
