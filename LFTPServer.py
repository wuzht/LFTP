import socket
import os
BUF_SIZE = 1024
SERVER_PORT = 12000
SEND_FILE_NAME = 'CarlaBruni.mp3'
SERVER_FOLDER = 'ServerFiles/'


# 接收到lget命令，向客户端发送文件
def lget(server_socket, client_address, large_file_name):
    print(large_file_name)

    # 发送数据包次数计数
    pkt_count = 0
    # 模式rb 以二进制格式打开一个文件用于只读。文件指针将会放在文件的开头。
    file_to_send = open(SERVER_FOLDER + large_file_name, 'rb')

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
        # print('接受自 ', client_address, ' 收到数据为 : ', data.decode('utf-8'))
        pkt_count += 1

    print(large_file_name, '发送完毕，发送数据包的数量：' + str(pkt_count))

def server_listening(server_socket):
    # 三次握手
    print("等待客户端发起连接...")
    message, client_address = server_socket.recvfrom(BUF_SIZE)
    print('来自', client_address, '的数据是: ', message.decode('utf-8'))

    # 来自客户端的命令，格式为[lsend|lget]#large_file_name，因此文件命名不允许含有#
    cmd = message.decode('utf-8').split('#')[0]
    large_file_name = message.decode('utf-8').split('#')[1]
    # 若命令是lget且文件不存在
    if cmd == 'lget' and (os.path.exists(SERVER_FOLDER + large_file_name) is False):
        server_socket.sendto('fileNotExists'.encode('utf-8'), client_address)
        return

    # 连接允许
    server_socket.sendto('连接允许'.encode('utf-8'), client_address)
    # 等待ACK
    message, client_address = server_socket.recvfrom(BUF_SIZE)
    print('来自', client_address, '的数据是: ', message.decode('utf-8'))

    if cmd == 'lget':
        lget(server_socket, client_address, large_file_name)

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
