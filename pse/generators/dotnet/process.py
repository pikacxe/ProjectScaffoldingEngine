import subprocess


def run_dotnet(args, cwd=None):
    command = ["dotnet", *args]
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
    )

    if result.returncode == 0:
        return result

    details = "\n".join(
        part.strip()
        for part in (result.stdout, result.stderr)
        if part and part.strip()
    )
    command_text = " ".join(command)

    if details:
        raise RuntimeError(f"Command failed ({result.returncode}): {command_text}\n{details}")

    raise RuntimeError(f"Command failed ({result.returncode}): {command_text}")
