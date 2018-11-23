import socket
import re
import os
BUF_SIZE = 1024
# SERVER_ADDR = ('127.0.0.1', 12000)
SERVER_PORT = 12000
CLIENT_FOLDER = 'ClientFiles/'   # 接收文件夹


def lsend(client_socket, server_addr, file_name):
    print("LFTP lsend", server_addr, file_name)


def lget(client_socket, server_address, large_file_name):
    print("LFTP lget", server_address, large_file_name)
    # 创建文件。模式wb 以二进制格式打开一个文件只用于写入。如果该文件已存在则打开文件，
    # 并从开头开始编辑，即原有内容会被删除。如果该文件不存在，创建新文件。
    file_to_recv = open(CLIENT_FOLDER + large_file_name, 'wb')
    # 接收数据包次数计数
    pkt_count = 0

    # 发送ACK 注意要做好所有准备(比如创建文件)后才向服务端发送ACK
    client_socket.sendto('ACK'.encode('utf-8'), server_address)

    # 开始接收数据包
    while True:
        # 用缓冲区接收文件
        data, server_address = client_socket.recvfrom(BUF_SIZE)
        if str(data) != "b'end'":  # 'end'为结束标志
            file_to_recv.write(data)
        else:
            break  # 接受到结束通知,结束循环
        # 向服务端发送ACK
        client_socket.sendto('ACK'.encode('utf-8'), server_address)
        pkt_count += 1

    file_to_recv.close()
    print('成功接收的数据包数量：' + str(pkt_count))


def connection_request(client_socket, server_addr, cmd, large_file_name):
    # 三次握手
    # 连接请求，格式为[lsend|lget]#large_file_name，因此文件命名不允许含有#
    client_socket.sendto((cmd + '#' + large_file_name).encode('utf-8'), server_addr)
    # 接收连接允许报文
    message, server_address = client_socket.recvfrom(BUF_SIZE)
    print('来自', server_address, '的数据是: ', message.decode('utf-8'))

    # 若服务端该文件不存在，退出程序
    if message.decode('utf-8') == 'fileNotExists':
        exit(2)

    # 注意要做好所有准备(比如创建文件)后才向服务端发送ACK
    if cmd == 'lget':
        lget(client_socket, server_address, large_file_name)


def read_command(client_socket):
    print('请输入命令: LFTP [lsend | lget] server_addr large_file_name')
    pattern = re.compile(r"(LFTP) (lsend|lget) (\S+) (\S+)")
    # LFTP lget 127.0.0.1 CarlaBruni.mp3
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
        print('文件夹', CLIENT_FOLDER, '不存在，请先创建！')
        exit(1)

    # 创建客户端socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # 客户端输入命令
    read_command(client_socket)

    # 关闭客户端socket
    client_socket.close()


if __name__ == "__main__":
    main()
