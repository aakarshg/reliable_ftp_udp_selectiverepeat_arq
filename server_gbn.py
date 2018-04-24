import socket
import struct
import random
import sys


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


def ack_make(seq_num):
    # 43690 is  1010101010101010 in decimal
    ackPacket = struct.pack('!IHH', seq_num, 0, 43690)  # SEQUENCE NUMBER BEING ACKED
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
    if len(sys.argv) >=3: # only if all arguments are given
        port = int(sys.argv[1])
        file_name = sys.argv[2]
        drop_prob = float(sys.argv[3])
    else: # otherwise we're gonna use the default values
        port = 7735 # 7735 temporarily changing
        file_name = 'output.txt'
        drop_prob = 0.1

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
            if random.uniform(0, 1) > drop_prob:  # packet accepted
                if sequence_number == prev_sequence_number + 1: # Check in sequence
                    packet_ack = ack_make(sequence_number)
                    Server_Socket.sendto(packet_ack, Client_Address)
                    if data == 'eof':
                        data_flag = False
                        print 'End of file command in data format received in Seq No' + str(sequence_number)
                        break
                    file_writer.write(data)
                    prev_sequence_number = sequence_number
                else:
                    print 'Out of order packet lost, Sequence Number = ' + str(sequence_number)
                    pass
            else:
                print 'Packet Loss, Sequence Number =' + str(sequence_number)

    print 'Complete file received - Closing connection'
    file_writer.close()
    Server_Socket.close()


if __name__ == '__main__':
    main()
