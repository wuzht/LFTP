# encoding:utf-8
import socket
import os
import struct
import threading
import sys
import random
BUF_SIZE = 1500
FILE_BUF_SIZE = 1024
SERVER_PORT = 12000
SERVER_FOLDER = 'ServerFiles/'
RCV_WINDOW_SIZE = 1000
SND_WINDOW_SIZE = 800
threadLock = threading.Lock()
dummy_address = ('150.10.10.2', 65351)

# 传输文件时的数据包格式(序列号，确认号，文件结束标志，1024B的数据)
# pkt_value = (int seq, int ack, int end_flag 1024B的byte类型 data)
pkt_struct = struct.Struct('III1024s')


# 接收到lget命令，向客户端发送文件
def lget(server_socket, client_address, large_file_name):
    print('正在发送', large_file_name)
    # 模式rb 以二进制格式打开一个文件用于只读。文件指针将会放在文件的开头。
    file_to_send = open(SERVER_FOLDER + large_file_name, 'rb')
    # 发送数据包次数计数
    pkt_count = 0

    # 发送缓冲区
    data_group = []
    for i in range(SND_WINDOW_SIZE):
        data_group.append(file_to_send.read(FILE_BUF_SIZE))
        if str(data_group[len(data_group) - 1]) == "b''":
            break

    send_base = 0
    # 用缓冲区循环发送数据包
    while True:
        send_package_num = 0

        # 将元组打包发送
        global is_exit
        is_exit = False
        is_end = False
        new_threading = threading.Thread(target=listen_package, args=(server_socket, 0))
        new_threading.start()
        for i in range(SND_WINDOW_SIZE):
            if is_full or pkt_count == len(data_group) - 1:
                break

            if str(data_group[i]) != "b''":  # b''表示文件读完
                end_flag = 0
                server_socket.sendto(pkt_struct.pack(*(pkt_count + i, int(threading.currentThread().ident), end_flag, data_group[i])),
                                     client_address)
                # print(sys._getframe().f_lineno, "sending", pkt_count + i)
                send_package_num += 1
            else:
                is_end = True
                end_flag = 1  # 发送的结束标志为1，表示文件已发送完毕
                server_socket.sendto(pkt_struct.pack(*(pkt_count + i, int(threading.currentThread().ident), end_flag, 'end'.encode('utf-8'))),
                                     client_address)
                threadLock.acquire()
                is_exit = True
                threadLock.release()
                # 等待ACK
                try:
                    new_threading.join()
                    ack_data_, client_address = server_socket.recvfrom(BUF_SIZE)
                    try:
                        ack_num = int(ack_data_.decode('utf-8'))
                        pkt_count = ack_num
                        print(sys._getframe().f_lineno, pkt_count)
                    except ValueError as e:
                        print(sys._getframe().f_lineno, e)
                        if str(ack_data_.decode('utf-8')) == str('isFull'):
                            try:
                                ack_data_, client_address = server_socket.recvfrom(BUF_SIZE)
                            except:
                                print(sys._getframe().f_lineno, e)
                                pkt_count = pkt_count + i
                                break
                        else:
                            pkt_count = pkt_count + i
                            break
                    break
                except socket.timeout as e:
                    print(sys._getframe().f_lineno, e)
                    pkt_count = pkt_count + i
                    break
                except ConnectionError as e:
                    print(sys._getframe().f_lineno, "pkt_count", pkt_count)
                    file_to_send.close()
                    print(sys._getframe().f_lineno, large_file_name, '发送完毕，发送数据包的数量：' + str(pkt_count), e)
                    break

        print(sys._getframe().f_lineno, "pkt_count sndbase lendata", pkt_count, send_base, len(data_group))
        if is_end:
            if pkt_count == send_base + len(data_group) - 1:
                print(sys._getframe().f_lineno, "return")
                return
            else:
                is_end = False
                continue

        threadLock.acquire()
        is_exit = True
        threadLock.release()
        new_threading.join()

        # 等待接收端ACK,这里只会发送一个ACK，收到的ACK的值为需要的部分的开始
        try:
            ack_data_, client_address = server_socket.recvfrom(BUF_SIZE)
            while True:
                get_data = str(ack_data_.decode('utf-8'))
                if get_data.isdigit():
                    ack_num = int(get_data)
                    print(sys._getframe().f_lineno, "ack_num", ack_num)
                    pkt_count = ack_num
                    break
                else:
                    pkt_count = pkt_count
                    ack_data_, client_address = server_socket.recvfrom(BUF_SIZE)

        except socket.timeout as e:
            print(sys._getframe().f_lineno, e)
            pkt_count = pkt_count
        except ConnectionResetError as e:
            print(sys._getframe().f_lineno, e)
            break

        print(sys._getframe().f_lineno, "pkt_count", pkt_count)

        # 更新data_group
        for i in range(pkt_count - send_base):
            del data_group[0]
        while len(data_group) < SND_WINDOW_SIZE:
            data_group.append(file_to_send.read(FILE_BUF_SIZE))
            if str(data_group[len(data_group) - 1]) == "b''":
                break
        send_base = pkt_count

    file_to_send.close()
    print(large_file_name, '发送完毕，发送数据包的数量：' + str(pkt_count))


def listen_package(server_socket, ack_type):
    global is_full
    is_full = False
    if ack_type == 0:
        # 循环接收，直到传输结束
        while not is_exit:
            try:
                ack_data_, client_address = server_socket.recvfrom(BUF_SIZE)
                if str(ack_data_.decode('utf-8')) == "isFull":
                    is_full = True
                print(sys._getframe().f_lineno, "listen_package", ack_data_.decode('utf-8'))
                break
            except socket.timeout as e:
                threadLock.acquire()
                if is_exit:
                    threadLock.release()
                    break
                else:
                    threadLock.release()
            except ConnectionResetError as e:
                print(e)
                break


# 接收到lsend命令，客户端向服务端发送文件
def lsend(server_socket, client_address, large_file_name):

    print('正在接收', large_file_name)
    # 创建文件。模式wb 以二进制格式打开一个文件只用于写入。如果该文件已存在则打开文件，
    # 并从开头开始编辑，即原有内容会被删除。如果该文件不存在，创建新文件。
    file_to_recv = open(SERVER_FOLDER + large_file_name, 'wb')

    # 发送接收允许
    server_socket.sendto('接收允许'.encode('utf-8'), client_address)

    need_ack = 0
    end_flag = 0
    # 开始接收数据包
    while True:
        # 用缓冲区接收数据包
        buffer_receive = []

        package_num = 0
        while len(buffer_receive) <= RCV_WINDOW_SIZE:
            try:
                packed_data_, client_address_ = server_socket.recvfrom(BUF_SIZE)
                if package_num > 600 and random.randint(0, 100) > 96:  # 模拟丢包
                    continue
                buffer_receive.append(packed_data_)
                package_num += 1
            except Exception as e:
                print(sys._getframe().f_lineno, e)
                break

        # 窗口满了，向发送端发送
        if package_num != 0:
            print(sys._getframe().f_lineno, "full")
            server_socket.sendto('isFull'.encode('utf-8'), client_address)

        # 从buffer_receive里读包，写到文件里
        while len(buffer_receive) > 0:
            data_ = buffer_receive[0]
            unpacked_data = pkt_struct.unpack(data_)
            seq_num = unpacked_data[0]

            if seq_num != need_ack:  # 收到乱序的数据包，则不再写入文件，跳出循环
                break
            ack_num = unpacked_data[1]
            end_flag = unpacked_data[2]
            data = unpacked_data[3]
            buffer_receive.remove(data_)
            if seq_num == need_ack:
                if end_flag != 1:
                    file_to_recv.write(data)
                    need_ack += 1
                else:
                    break  # 结束标志为1,结束循环

        print(sys._getframe().f_lineno, "need_ack", need_ack)

        if random.randint(0, 99) > 90:  # 模拟ACK丢包
            server_socket.sendto(str(need_ack).encode('utf-8'), dummy_address)
        else:
            server_socket.sendto(str(need_ack).encode('utf-8'), client_address)
        if end_flag == 1:
            break

    file_to_recv.close()
    # print(len(buffer_receive))

    print('成功接收的数据包数量：' + str(need_ack))


def serve_client(client_address, message):
    # 创建新的服务端socket为客户端提供服务
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.settimeout(2)

    # 来自客户端的命令，格式为[lsend|lget]#large_file_name，因此文件命名不允许含有#
    cmd = message.decode('utf-8').split('#')[0]
    large_file_name = message.decode('utf-8').split('#')[1]

    if cmd == 'lget':
        server_socket.settimeout(2)
        # 文件不存在，并告知客户端
        if os.path.exists(SERVER_FOLDER + large_file_name) is False:
            server_socket.sendto('fileNotExists'.encode('utf-8'), client_address)
            # 关闭socket
            server_socket.close()
            return

        # TODO: 在此要把各样工作准备好，再发送连接允许

        # 连接允许
        send_words = '连接允许,' + str(threading.currentThread().ident)
        server_socket.sendto(send_words.encode('utf-8'), client_address)
        # 等待ACK
        while True:
            try:
                message, client_address = server_socket.recvfrom(BUF_SIZE)
                break
            except socket.timeout as e:
                continue
        print('来自', client_address, '的数据是: ', message.decode('utf-8'))

        lget(server_socket, client_address, large_file_name)
    elif cmd == 'lsend':
        server_socket.settimeout(1)
        # 连接允许
        send_words = '连接允许,' + str(threading.currentThread().ident)
        server_socket.sendto(send_words.encode('utf-8'), client_address)
        # 等待ACK
        while True:
            try:
                message, client_address = server_socket.recvfrom(BUF_SIZE)
                break
            except socket.timeout as e:
                continue
        print('来自', client_address, '的数据是: ', message.decode('utf-8'))

        # TODO: 在此要把各样工作准备好，再发送接收允许(在lsend内)

        lsend(server_socket, client_address, large_file_name)

    # 关闭socket

    print("close")
    server_socket.close()


def main():
    # 检查接收文件夹是否存在
    if os.path.exists(SERVER_FOLDER) is False:
        print('创建文件夹', SERVER_FOLDER)
        os.mkdir(SERVER_FOLDER)

    # 创建服务端主socket，周知端口号为SERVER_PORT
    server_main_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_main_socket.bind(('', SERVER_PORT))
    server_main_socket.settimeout(2)

    # global wsnd
    # wsnd = WINDOW_SIZE

    global address
    address = []

    while True:
        print('正在运行的线程数量：', threading.activeCount())
        # 服务端主socket等待客户端发起连接
        print("等待客户端发起连接...")
        while True:
            try:
                message, client_address = server_main_socket.recvfrom(BUF_SIZE)
                break
            except socket.timeout as e:
                continue
        print('来自', client_address, '的数据是: ', message.decode('utf-8'))

        # 创建新的线程，处理客户端的请求

        address.append(client_address)
        new_thread = threading.Thread(target=serve_client, args=(client_address, message))
        new_thread.start()



if __name__ == "__main__":
    main()
