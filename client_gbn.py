import sys
import socket
import time
import struct
import threading
import os

lock_window = threading.Lock()
time_retransmit = 0.05
packets_data = []
timestamp_array =[]
ack_prev = -1
packets_transit = 0


def checksum_calculate(data):
    sum_element = 0
    for i in range(0, len(data), 2):
        if i + 1 < len(data):
            element_16bits = ord(data[i]) + (ord(data[i + 1]) << 8)
            k = sum_element + element_16bits
            a = (k & 0xffff)
            b = k >> 16
            sum_element = a + b  # carry around addition
    return ~sum_element & 0xffff


def packet_make(sequence_current,data_packet):
    check_sum = checksum_calculate(data_packet)
    header = struct.pack('!IHH',sequence_current, check_sum, 21845)
    packet = header + data_packet
    return packet

def file_break_packets(file_name,MSS):
    global packets_data

    if os.path.isfile(file_name):

        data_packet = ''
        sequence_current = 0

        file_reader = open(file_name, 'rb')
        read_onebyte = file_reader.read(1)
        data_packet += read_onebyte

        while data_packet != '':
            if len(data_packet) == MSS or read_onebyte == '':
                packets_data.append(packet_make(sequence_current,data_packet)) # send packet by adding header information
                data_packet = ''
                sequence_current += 1
            read_onebyte = file_reader.read(1)
            data_packet += read_onebyte

        data_packet = 'eof'
        packets_data.append(packet_make(sequence_current, data_packet))
        file_reader.close()
    else:
        print 'File dosenot exist in the given location. Please Check \n'
        sys.exit()


def rdt_send(server_ip, Client_Socket, window_size):
    print 'rdt_send thread started'
    global packets_data
    global ack_prev
    global packets_transit
    global timestamp_array

    timestamp_array = [None]*len(packets_data)
    while (ack_prev + 1) < len(packets_data):
        lock_window.acquire()
        if packets_transit < window_size and ((ack_prev + packets_transit + 1) < len(packets_data)):            #Send More Packets
            Client_Socket.sendto(packets_data[ack_prev + packets_transit + 1], server_ip)
            timestamp_array[ack_prev + packets_transit + 1] = time.time()
            packets_transit += 1
        if packets_transit > 0:
            if (time.time() - timestamp_array[ack_prev + 1]) > time_retransmit:
                #print 'Time out, Sequence Number =' + str(ack_prev+1) #commented out for tasks
                packets_transit = 0
        lock_window.release()



def ack_packet_split(data_ack):
    Ack = struct.unpack('!IHH', data_ack)
    seq_num = Ack[0]
    if Ack[1] == 0 and Ack[2] == 43690:
        valid_ack = True
    else:
        print 'Invalid Frame as Header Format doesnt match'
        valid_ack = False
    return valid_ack, seq_num


def receive_ack(Client_Socket):
    print "Client Thread to Receive Acknowledgements Started \n"
    global ack_prev
    global packets_transit
    global timestamp_array
    global packets_data

    try:
        while (ack_prev + 1) < len(packets_data):
            if packets_transit > 0:
                data_ack, server_ip = Client_Socket.recvfrom(2048)
                Valid_frame, Sequence_Number = ack_packet_split(data_ack)
                lock_window.acquire()
                if Valid_frame:
                    if ack_prev+1 == Sequence_Number:
                        ack_prev += 1
                        packets_transit -= 1
                    else:
                        packets_transit = 0
                else:
                    packets_transit = 0

                lock_window.release()

    except:
        print "Server closed its connection"
        Client_Socket.close()
        sys.exit()


def main():
    if len(sys.argv) >=5: # only if all arguments are given:
        server_host_name = sys.argv[1]
        server_port = int(sys.argv[2])
        file_name = sys.argv[3]
        window_size= int(sys.argv[4])
        MSS = int(sys.argv[5])
    else:
        server_host_name = '127.0.0.1'
        server_port = 7735
        file_name = 'input.txt'
        window_size= 16
        MSS = 500

    server_ip = (server_host_name, server_port)
    host_ip = socket.gethostbyname(socket.gethostname())
    Client_Socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    Client_Port = 2346 # arbitary
    Client_Socket.bind(( host_ip , Client_Port))
    print 'IP address of the client is ' +host_ip + ' it is running at port' + str(Client_Port) + 'and server ip addr is ' +str(server_ip)
    file_break_packets(file_name,MSS)

    timestamp_start = time.time()

    thread_receive_ack = threading.Thread(target=receive_ack, args=(Client_Socket,))
    thread_rdt_send = threading.Thread(target=rdt_send,args=(server_ip, Client_Socket, window_size))

    thread_receive_ack.start()
    thread_rdt_send.start()
    thread_receive_ack.join()
    thread_rdt_send.join()
    timestamp_end = time.time()
    print 'Ending Program'
    print 'Total Time Taken:' + str(timestamp_end - timestamp_start) + 'MSS size' + str(MSS) # for task 2
    #print 'Total Time Taken:' + str(timestamp_end - timestamp_start)
    if Client_Socket:
        Client_Socket.close()

if __name__ == '__main__':
    main()
