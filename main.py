import re
import os

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


def lsend(server_addr, file_name):
    print("LFTP lsend", server_addr, file_name)


def lget(server_addr, file_name):
    print("LFTP lget", server_addr, file_name)


def read_command():
    print('scanf()')
    pattern = re.compile(r"(LFTP) (lsend|lget) (\S+) (\S+)")
    # cmd = 'LFTP - lget errors, 4.4.4.4 warnings'
    cmd = input()
    match = pattern.match(cmd)
    if match:
        if match.group(2) == 'lsend':
            lsend(match.group(3), match.group(4))
        elif match.group(2) == 'lget':
            lget(match.group(3), match.group(4))
        else:
            print('[Error] Invalid command!')
    else:
        print('[Error] Invalid command!')


def main():
    usage = Usage("hello")
    print(usage.msg)
    # cmd = input()
    # if cmd == 1:
    #     lsend('127.0.0.1', 'largefile.zip')
    # else:
    #     lget('127.0.0.1', 'largefile.zip')
    # read_command()

    str = "this is string example....wow!!!"
    str = "lget#Carla Bruni - Chez Keith et Anita.mp3"
    print(str.split('#')[1])
    print(str.split('i', 1))
    print(str.split('w'))

    print(os.path.exists('ClientFiles/CarlaBruni.mp3'))
    print(os.path.exists('Carla Bruni - Chez Keith et Anita.mp3'))


if __name__ == "__main__":
    main()
