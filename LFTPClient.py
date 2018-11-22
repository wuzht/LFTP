import socket
BUF_SIZE = 1024
server_addr = ('127.0.0.1', 12000)
RECV_FOLDER = 'FileRecv/'   # 接收文件夹


def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # 三次握手
    # 连接请求
    client_socket.sendto('连接请求。请告诉我文件名称'.encode('utf-8'), server_addr)
    # 接收连接允许报文（文件名称）
    data, server_address = client_socket.recvfrom(BUF_SIZE)
    recv_file_name = data.decode('utf-8')
    print('来自', server_address, ' 的数据是: ', recv_file_name)
    # 创建文件。模式wb 以二进制格式打开一个文件只用于写入。如果该文件已存在则打开文件，
    # 并从开头开始编辑，即原有内容会被删除。如果该文件不存在，创建新文件。
    file_to_recv = open(RECV_FOLDER + recv_file_name, 'wb')
    # 接收数据包次数计数
    pkt_count = 0
    # 发送ACK
    client_socket.sendto('ACK. 可以开始给我发送数据了'.encode('utf-8'), server_addr)

    # 开始传输数据包
    while True:
        # 用缓冲区接收文件
        data, server_address = client_socket.recvfrom(BUF_SIZE)
        if str(data) != "b'end'":   # 'end'为结束标志
            file_to_recv.write(data)
        else:
            break   # 接受到结束通知,结束循环
        # 向服务端发送ACK
        client_socket.sendto('ACK'.encode('utf-8'), server_address)
        pkt_count += 1

    print('成功接收的数据包数量：' + str(pkt_count))
    file_to_recv.close()
    client_socket.close()


if __name__ == "__main__":
    main()
