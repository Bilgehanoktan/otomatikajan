from bilgeapi_api_key_admin import main
import sys


def _with_command(command: str, argv: list[str]) -> list[str]:
    global_args = []
    command_args = []
    index = 0
    while index < len(argv):
        if argv[index] in {"--base-url", "--admin-api-key"} and index + 1 < len(argv):
            global_args.extend([argv[index], argv[index + 1]])
            index += 2
        else:
            command_args.append(argv[index])
            index += 1
    return [*global_args, command, *command_args]


if __name__ == "__main__":
    raise SystemExit(main(_with_command("revoke", sys.argv[1:])))
