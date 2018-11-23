import socket
import os
BUF_SIZE = 1024
SERVER_PORT = 12000
SEND_FILE_NAME = 'CarlaBruni.mp3'
SERVER_FOLDER = 'ServerFiles/'


# 接收到lget命令，向客户端发送文件
def lget(server_socket, client_address, large_file_name):
    print(large_file_name)
    # 模式rb 以二进制格式打开一个文件用于只读。文件指针将会放在文件的开头。
    file_to_send = open(SERVER_FOLDER + large_file_name, 'rb')
    # 发送数据包次数计数
    pkt_count = 0

    # 用缓冲区循环发送文件
    while True:
        data = file_to_send.read(BUF_SIZE)
        if str(data) != "b''":  # b''表示文件读完
            server_socket.sendto(data, client_address)
        else:
            # 把'end'发送给客户端，表示文件已发送完毕
            server_socket.sendto('end'.encode('utf-8'), client_address)
            break
        # 等待客户端ACK
        data, client_address = server_socket.recvfrom(BUF_SIZE)
        # print('接受自 ', client_address, '收到数据为 : ', data.decode('utf-8'))
        pkt_count += 1

    file_to_send.close()
    print(large_file_name, '发送完毕，发送数据包的数量：' + str(pkt_count))


# 接收到lsend命令，客户端向服务端发送文件
def lsend(server_socket, client_address, large_file_name):
    print(large_file_name)
    # 创建文件。模式wb 以二进制格式打开一个文件只用于写入。如果该文件已存在则打开文件，
    # 并从开头开始编辑，即原有内容会被删除。如果该文件不存在，创建新文件。
    file_to_recv = open(SERVER_FOLDER + large_file_name, 'wb')
    # 接收数据包次数计数
    pkt_count = 0

    # 发送接收允许
    server_socket.sendto('接收允许'.encode('utf-8'), client_address)

    # 开始接收数据包
    while True:
        # 用缓冲区接收文件
        data, client_address = server_socket.recvfrom(BUF_SIZE)
        if str(data) != "b'end'":  # 'end'为结束标志
            file_to_recv.write(data)
        else:
            break  # 接受到结束通知,结束循环
        # 向客户端发送ACK
        server_socket.sendto('ACK'.encode('utf-8'), client_address)
        pkt_count += 1

    file_to_recv.close()
    print('成功接收的数据包数量：' + str(pkt_count))


def server_listening(server_socket):
    # 三次握手
    print("等待客户端发起连接...")
    message, client_address = server_socket.recvfrom(BUF_SIZE)
    print('来自', client_address, '的数据是: ', message.decode('utf-8'))

    # 来自客户端的命令，格式为[lsend|lget]#large_file_name，因此文件命名不允许含有#
    cmd = message.decode('utf-8').split('#')[0]
    large_file_name = message.decode('utf-8').split('#')[1]

    if cmd == 'lget':
        # 文件不存在，并告知客户端
        if os.path.exists(SERVER_FOLDER + large_file_name) is False:
            server_socket.sendto('fileNotExists'.encode('utf-8'), client_address)
            return

        # TODO: 在此要把各样工作(如分配线程等)准备好，再发送连接允许

        # 连接允许
        server_socket.sendto('连接允许'.encode('utf-8'), client_address)
        # 等待ACK
        message, client_address = server_socket.recvfrom(BUF_SIZE)
        print('来自', client_address, '的数据是: ', message.decode('utf-8'))

        lget(server_socket, client_address, large_file_name)
    elif cmd == 'lsend':
        # 连接允许
        server_socket.sendto('连接允许'.encode('utf-8'), client_address)
        # 等待ACK
        message, client_address = server_socket.recvfrom(BUF_SIZE)
        print('来自', client_address, '的数据是: ', message.decode('utf-8'))

        # TODO: 在此要把各样工作(如分配线程等)准备好，再发送接收允许(在lsend内)

        lsend(server_socket, client_address, large_file_name)


def main():
    # 检查接收文件夹是否存在
    if os.path.exists(SERVER_FOLDER) is False:
        print('文件夹', SERVER_FOLDER, '不存在，请先创建！')
        exit(1)

    # 创建服务端socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('', SERVER_PORT))

    while True:
        server_listening(server_socket)

    # 关闭服务端socket
    server_socket.close()


if __name__ == "__main__":
    main()
