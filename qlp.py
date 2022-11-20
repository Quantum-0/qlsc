import socket

# low level

__QLP_PORT__ = 52075


def calc_crc(data: bytes) -> int:
    crc = 0x75
    for b in data:
        crc ^= b
    return crc


def send_raw(data: bytes, add_crc: bool):
    if add_crc:
        data += calc_crc(data).to_bytes(1, 'big')
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(data, ("255.255.255.255", __QLP_PORT__))


def send_packet(data: bytes, proto_ver: int = 1, packet_type: int = 1):
    packet = b'QLP' + proto_ver.to_bytes(1, 'big') + packet_type.to_bytes(1, 'big') + data
    send_raw(packet, add_crc=True)


def send_anybody_here():
    send_packet(b'ABH')


def listen():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    sock.bind(("", __QLP_PORT__))
    while True:
        data, addr = sock.recvfrom(1024)
        print(f'[{addr}]: {data}')
