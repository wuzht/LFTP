# LFTP
Computer Networks Midterm Project

A network application, LFTP, to support large file transfer between two computers in the Internet.

## 文件

* `LFTPServer.py` LFTP服务端

* `LFTPClient.py` LFTP客户端

## 文件夹

收发的文件放在下面的两个文件夹。运行时若以下两个文件夹不存在，则自动建立：

 * `ServerFiles` 服务端(要接收或发送)的文件存放在ServerFiles
 * `ClinetFiles` 客户端(要接收或发送)的文件存放在ClientFiles

 注意要传输的文件命名不能有空格和`#`

 ## LFTP协议数据包格式

 使用python的struct模块打包数据，形成LFTP数据包发送

 定义`pkt_struct = struct.Struct('III1024s')`

 暂时定义的数据包格式(实现的过程中根据需要调整):

 * `seq` int类型，序列号
 * `ack` int类型，确认号
 * `end_flag` int类型，文件结束标志，为1时表示文件发送完毕
 * `data` 1024字节的byte类型

 需要添加struct模块`import struct`

 使用方法参照博客：https://www.cnblogs.com/leomei91/p/7602603.html

 ## 多线程

 支持同时多客户端文件收发

 服务端周知端口号为12000，收到客户端请求后，创建新的服务端线程(新的socket, 新的端口号)处理对应客户的请求

 使用python3的`threading`模块，方法参考：http://www.runoob.com/python3/python3-multithreading.html

 
