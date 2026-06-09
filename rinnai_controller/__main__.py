import json

from .core import Controller


def main() -> int:
    controller = Controller()
    print(json.dumps(controller.getData(True, True), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
