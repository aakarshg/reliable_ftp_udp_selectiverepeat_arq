import socket
import struct
import random
import sys


data_packet = []


def checksum_verify(data,check_sum):
    sum_element = 0
    for i in range(0, len(data), 2):
        if i + 1 < len(data):
            element_16bits = ord(data[i]) + (ord(data[i + 1]) << 8)
            k = sum_element + element_16bits
            a = (k & 0xffff)
            b = k >> 16
            sum_element = a + b  # carry around addition
    checksum_received  = sum_element & 0xffff
    check_sum_verified = checksum_received  & check_sum
    return check_sum_verified


def ack_make(seq_num, end = False):
    # 43690 is  1010101010101010 in decimal
    if end == False:
        ackPacket = struct.pack('!IHH', seq_num, 0, 43690)  # SEQUENCE NUMBER BEING ACKED
    else:
        print "sending end_of_file" #for debugging purpose
        ackPacket = struct.pack('!IHH', seq_num, 2, 43690) # sending eof received
    return ackPacket

def nack_make(seq_num):
    # 43690 is  1010101010101010 in decimal
    ackPacket = struct.pack('!IHH', seq_num, 1, 43690)  # SEQUENCE NUMBER BEING ACKED
    return ackPacket


def packet_extract(packet_data):
    packet_header = struct.unpack('!IHH', packet_data[0:8])
    seq_num = packet_header[0]
    check_sum = packet_header[1]
    data = packet_data[8:]
    valid_frame = False
    check_sum_verified = checksum_verify(data,check_sum)
    #print data
    # 21845 is  0101010101010101 in decimal
    if check_sum_verified == 0 and packet_header[2] == 21845:
        valid_frame = True
    return valid_frame, seq_num, data


def main():
    cur_window_pointer = 0
    if len(sys.argv) >=3: # only if all arguments are given
        port = int(sys.argv[1])
        file_name = sys.argv[2]
        drop_prob = float(sys.argv[3])
        window_size = int(sys.argv[4])
    else: # otherwise we're gonna use the default values
        port = 7735 # 7735 temporarily changing
        file_name = 'output.txt'
        drop_prob = 0.05
        window_size = 500

    Server_Socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #SOCK_DGRAM for using udp
    ip = socket.gethostbyname(socket.gethostname()) #Get the IP address
    print 'IP address of the server is ' +ip + ' it is running at port' + str(port)
    Server_Socket.bind((ip, port))
    prev_sequence_number = -1

    file_writer = open(file_name, 'wb')
    data_flag = True
    while data_flag:
        packet_data, Client_Address = Server_Socket.recvfrom(2048)
        valid_frame, sequence_number, data = packet_extract(packet_data)
        if valid_frame:
            if random.uniform(0, 1) < drop_prob and data!='eof':  # packet dropped
                print 'Packet Loss, Sequence Number =' + str(sequence_number)
                packet_ack = nack_make(sequence_number)
                Server_Socket.sendto(packet_ack, Client_Address)
            else:
                if sequence_number == prev_sequence_number + 1: # Check in sequence
                    packet_ack = ack_make(sequence_number)
                    Server_Socket.sendto(packet_ack, Client_Address)
                    if data == 'eof':
                        packet_ack = ack_make(sequence_number, True)
                        Server_Socket.sendto(packet_ack, Client_Address)
                        file_writer = open('server.txt','wb')
                        for x in data_packet:
                            file_writer.write(x)
                        data_flag = False
                        print 'End of file command in data format received in Seq No' + str(sequence_number)
                        break
                    data_packet.append(data) # create a mapping
                    file_writer.write(data)
                    prev_sequence_number = sequence_number
                else:
                    # implies that previous packet was dropped
                    if data != 'eof':
                        if sequence_number > len(data_packet)-1:
                            while sequence_number > len(data_packet)-1:
                                data_packet.append(0)
                        else:
                            data_packet[sequence_number] = data
                    if data == 'eof':
                        packet_ack = ack_make(sequence_number, True)
                        Server_Socket.sendto(packet_ack, Client_Address)
                        data_flag = False
                        print 'End of file command in data format received in Seq No' + str(sequence_number)
                        break
                    file_writer.write(data)
                    packet_ack = ack_make(sequence_number)
                    Server_Socket.sendto(packet_ack, Client_Address)
    print 'Complete file received - Closing connection'
    file_writer.close()
    Server_Socket.close()


if __name__ == '__main__':
    main()
