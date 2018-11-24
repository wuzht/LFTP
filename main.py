import re
import os
import binascii
import struct
import sys
import threading
import time
CLIENT_FOLDER = 'ClientFiles/'
SERVER_FOLDER = 'ServerFiles/'
large_file_name = 'CarlaBruni.mp3'
BUF_SIZE = 1500
READ_BUF_SIZE = 1024





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

def struct_test():
    # 模式rb 以二进制格式打开一个文件用于只读。文件指针将会放在文件的开头。
    file_to_send = open(SERVER_FOLDER + large_file_name, 'rb')
    data = file_to_send.read(BUF_SIZE)
    print(data)
    print(data.__sizeof__())
    print(sys.getsizeof(data))

    ack = 1
    seqNum = 2
    buf_size = 1024

    values = (ack, seqNum, buf_size, b'end')
    s = struct.Struct('III1024s')
    packed_data = s.pack(*values)
    unpacked_data = s.unpack(packed_data)
    print('Original values:', values)
    print('Format string :', s.format)
    print('Uses :', s.size, 'bytes')
    print('Packed Value :', binascii.hexlify(packed_data))
    print('Unpacked Type :', type(unpacked_data), ' Value:', unpacked_data)
    print('Data :', str(unpacked_data[3].decode('utf-8')), "fe")

    print(isinstance(packed_data, bytes))  # True
    print(unpacked_data[3] == data)  # True
    print(isinstance(data, bytes))  # True

exitFlag = 0

# 为线程定义一个函数
def print_time(threadName, delay, counter):
    while counter:
        if exitFlag:
            threadName.exit()
        time.sleep(delay)
        print ("%s: %s" % (threadName, time.ctime(time.time())))
        counter -= 1

# 从 threading.Thread 继承创建一个新的子类，并实例化后调用start()方法启动新线程，
# 即它调用了线程的 run() 方法
class myThread (threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter

    def run(self):
        print("开始线程：" + self.name)
        print_time(self.name, self.counter, 5)
        print("退出线程：" + self.name)

def main():
    usage = Usage("hello")
    print(usage.msg)

    # # 创建两个线程
    # thread1 = myThread(1, "Thread-1", 1)
    # thread2 = myThread(2, "Thread-2", 2)
    #
    # # 开启新线程
    # thread1.start()
    # thread2.start()
    # thread1.join()
    # thread2.join()
    # print("退出主线程")

    # os.mkdir('test/')




if __name__ == "__main__":
    main()
