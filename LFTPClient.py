# encoding:utf-8
import socket
import re
import os
import struct
import threading
import sys
import random
import time
BUF_SIZE = 1500
FILE_BUF_SIZE = 1024
SERVER_PORT = 12000
CLIENT_FOLDER = 'ClientFiles/'   # 接收文件夹

RCV_WINDOW_SIZE = 1000
SND_WINDOW_SIZE = 800
# wsnd = WINDOW_SIZE

threading_lock = threading.Lock()
dummy_address = ('150.10.10.2', 65351)

# 传输文件时的数据包格式(序列号，确认号，文件结束标志，1024B的数据)
# pkt_value = (int seq, int ack, int end_flag 1024B的byte类型 data)
pkt_struct = struct.Struct('III1024s')


def lsend(client_socket, server_address, large_file_name):
    print("LFTP lsend", server_address, large_file_name)
    # 发送数据包次数计数
    pkt_count = 0
    # 模式rb 以二进制格式打开一个文件用于只读。文件指针将会放在文件的开头。
    file_to_send = open(CLIENT_FOLDER + large_file_name, 'rb')

    data_group = []
    for i in range(SND_WINDOW_SIZE):
        data_group.append(file_to_send.read(FILE_BUF_SIZE))
        if str(data_group[len(data_group) - 1]) == "b''":
            break

    # 发送ACK 注意要做好所有准备(比如打开文件)后才向服务端发送ACK
    client_socket.sendto('ACK'.encode('utf-8'), server_address)

    # 等待服务端的接收允许
    message, server_address = client_socket.recvfrom(BUF_SIZE)
    print('来自', server_address, '的数据是: ', message.decode('utf-8'))

    print('正在发送', large_file_name)

    send_base = 0
    # 用缓冲区循环发送数据包
    cwnd = 1
    while True:
        send_package_num = 0

        # 将元组打包发送
        global is_exit
        is_exit = False
        is_end = False
        new_threading = threading.Thread(target=listen_package, args=(client_socket, 0))
        new_threading.start()
        for i in range(cwnd):

            if is_full or pkt_count == len(data_group) - 1 or i >= len(data_group):
                break

            if str(data_group[i]) != "b''":  # b''表示文件读完
                end_flag = 0
                client_socket.sendto(pkt_struct.pack(*(pkt_count+i, int(pid), end_flag, data_group[i])), server_address)
                send_package_num += 1
            else:
                is_end = True
                end_flag = 1  # 发送的结束标志为1，表示文件已发送完毕
                client_socket.sendto(pkt_struct.pack(*(pkt_count+i, int(pid), end_flag, 'end'.encode('utf-8'))), server_address)
                threading_lock.acquire()
                is_exit = True
                threading_lock.release()
                # 等待ACK
                try:
                    new_threading.join()
                    ack_data_, server_address = client_socket.recvfrom(BUF_SIZE)
                    ack_num = int(ack_data_.decode('utf-8'))
                    pkt_count = ack_num
                    break
                except socket.timeout as e:
                    pkt_count = pkt_count + i
                    break
                except ConnectionResetError as e:
                    pkt_count = pkt_count + i
                    return
                except ValueError as e:
                    pkt_count = pkt_count + i
                    break

        if is_end:
            if pkt_count == send_base + len(data_group) - 1:
                print(sys._getframe().f_lineno, "return")
                file_to_send.close()
                print(large_file_name, '发送完毕，发送数据包的数量：' + str(pkt_count))
                return
            else:
                is_end = False
                continue

        threading_lock.acquire()
        is_exit = True
        threading_lock.release()
        new_threading.join()

        # 等待服务端ACK,这里只会发送一个ACK，收到的ACK的值为需要的部分的开始
        try:
            ack_data_, server_address = client_socket.recvfrom(BUF_SIZE)
            while True:
                get_data = str(ack_data_.decode('utf-8'))
                if get_data.isdigit():
                    ack_num = int(get_data)
                    print(sys._getframe().f_lineno, "ack_num", ack_num)
                    pkt_count = ack_num
                    break
                else:
                    cwnd = 1
                    pkt_count = pkt_count
                    ack_data_, server_address = client_socket.recvfrom(BUF_SIZE)

        except socket.timeout as e:
            pkt_count = pkt_count
            cwnd = 1
        except ConnectionResetError as e:
            print(sys._getframe().f_lineno, e)
            break

        print(sys._getframe().f_lineno, "pkt_count", pkt_count)

        cwnd *= 2
        # 更新data_group
        for i in range(pkt_count - send_base):
            del data_group[0]
        while len(data_group) < SND_WINDOW_SIZE:
            data_group.append(file_to_send.read(FILE_BUF_SIZE))
            if str(data_group[len(data_group) - 1]) == "b''":
                break
        send_base = pkt_count



def listen_package(client_socket, ack_type):
    global is_full
    is_full = False
    if ack_type == 0:
        # 循环接收，直到传输结束
        while not is_exit:
            try:
                ack_data_, server_address = client_socket.recvfrom(BUF_SIZE)
                if str(ack_data_.decode('utf-8')) == "isFull":
                    is_full = True
                break
            except socket.timeout as e:
                threading_lock.acquire()
                if is_exit:
                    threading_lock.release()
                    break
                else:
                    threading_lock.release()
            except ConnectionResetError as e:
                print(e)
                return


def lget(client_socket, server_address, large_file_name):
    print("LFTP lget", server_address, large_file_name)
    # 创建文件。模式wb 以二进制格式打开一个文件只用于写入。如果该文件已存在则打开文件，
    # 并从开头开始编辑，即原有内容会被删除。如果该文件不存在，创建新文件。
    file_to_recv = open(CLIENT_FOLDER + large_file_name, 'wb')

    # 发送ACK 注意要做好所有准备(比如创建文件)后才向服务端发送ACK
    client_socket.sendto('ACK'.encode('utf-8'), server_address)
    need_ack = 0
    end_flag = 0
    print('正在接收', large_file_name)

    # 开始接收数据包
    while True:
        buffer_receive = []
        # 用缓冲区接收数据包
        package_num = 0
        while len(buffer_receive) <= RCV_WINDOW_SIZE:
            try:
                packed_data_, server_address_ = client_socket.recvfrom(BUF_SIZE)
                if package_num > 600 and random.randint(0, 100) > 96:    # 模拟丢包
                    continue
                buffer_receive.append(packed_data_)
                package_num += 1
            except Exception as e:
                print(sys._getframe().f_lineno, e)
                break

        # 窗口满了，向发送端发送
        if package_num != 0:
            print(sys._getframe().f_lineno ,"full")
            client_socket.sendto('isFull'.encode('utf-8'), server_address)

        # 从buffer_receive里读包，写到文件里
        while len(buffer_receive) > 0:
            data_ = buffer_receive[0]
            unpacked_data = pkt_struct.unpack(data_)
            seq_num = unpacked_data[0]

            if seq_num != need_ack:     # 收到乱序的数据包，则不再写入文件，跳出循环
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
                    need_ack += 1
                    break  # 结束标志为1,结束循环

        print(sys._getframe().f_lineno, "need_ack", need_ack)

        if random.randint(0, 99) > 90:  # 模拟ACK丢包
            client_socket.sendto(str(need_ack).encode('utf-8'), dummy_address)
        else:
            client_socket.sendto(str(need_ack).encode('utf-8'), server_address)
        if end_flag == 1:
            break

    file_to_recv.close()
    print('成功接收的数据包数量：' + str(need_ack))


def connection_request(client_socket, server_addr, cmd, large_file_name):
    # 若要发送的文件不存在，退出程序
    if cmd == 'lsend' and (os.path.exists(CLIENT_FOLDER + large_file_name) is False):
        print('要发送的文件不存在，退出程序')
        exit(2)

    # 三次握手
    # 连接请求，格式为[lsend|lget]#large_file_name，因此文件命名不允许含有#
    client_socket.sendto((cmd + '#' + large_file_name).encode('utf-8'), server_addr)
    # 接收连接允许报文
    while True:
        try:
            message, server_address = client_socket.recvfrom(BUF_SIZE)
            break
        except socket.timeout as e:
            continue
    global pid
    if len(message.decode('utf-8').split(',')) > 1:
        pid = message.decode('utf-8').split(',')[1]
    response = message.decode('utf-8').split(',')[0]
    print('来自', server_address, '的数据是: ', response)

    # 若服务端该文件不存在，退出程序
    if response == 'fileNotExists':
        exit(2)

    # 注意要做好所有准备(比如创建文件)后才向服务端发送ACK
    if cmd == 'lget':
        client_socket.settimeout(1)
        lget(client_socket, server_address, large_file_name)
    elif cmd == 'lsend':
        client_socket.settimeout(2)
        lsend(client_socket, server_address, large_file_name)


def read_command(client_socket):
    print('请输入命令: LFTP [lsend | lget] server_address large_file_name')
    pattern = re.compile(r"(LFTP) (lsend|lget) (\S+) (\S+)")
    # LFTP lget 127.0.0.1 CarlaBruni.mp3
    # LFTP lsend 127.0.0.1 CarlaBruni.mp3
    cmd = input()
    match = pattern.match(cmd)
    if match:
        cmd = match.group(2)
        server_ip = match.group(3)
        large_file_name = match.group(4)
        connection_request(client_socket, (server_ip, SERVER_PORT), cmd, large_file_name)
    else:
        print('[Error] Invalid command!')


def main():
    # 检查接收文件夹是否存在
    if os.path.exists(CLIENT_FOLDER) is False:
        print('创建文件夹', CLIENT_FOLDER)
        os.mkdir(CLIENT_FOLDER)

    # 创建客户端socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(4)


    # 客户端输入命令
    read_command(client_socket)

    # 关闭客户端socket
    client_socket.close()


if __name__ == "__main__":
    main()
