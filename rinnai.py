import json
from rinnai_controller import Controller


if __name__ == '__main__':
    rinnai = Controller()
    print(rinnai.getData(True, True))