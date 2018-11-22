import socket
BUF_SIZE = 1024
SERVER_PORT = 12000
SEND_FILE_NAME = 'Carla Bruni - Chez Keith et Anita.mp3'


def main():
    server_addr = ('', SERVER_PORT)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(server_addr)
    # 发送数据包次数计数
    pkt_count = 0
    # 模式rb 以二进制格式打开一个文件用于只读。文件指针将会放在文件的开头。
    file_to_send = open(SEND_FILE_NAME, 'rb')

    # 三次握手
    print("等待客户端发起连接...")
    message, client_address = server_socket.recvfrom(BUF_SIZE)
    print('来自', client_address, ' 的数据是: ', message.decode('utf-8'))
    # 连接允许，把文件名称告诉客户端
    server_socket.sendto(SEND_FILE_NAME.encode('utf-8'), client_address)
    # 等待ACK
    message, client_address = server_socket.recvfrom(BUF_SIZE)
    print('来自', client_address, ' 的数据是: ', message.decode('utf-8'))

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

    print('发送数据包的数量：' + str(pkt_count))
    server_socket.close()


if __name__ == "__main__":
    main()
