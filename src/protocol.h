#include <WiFiUdp.h>

const unsigned int localPort = 52075;
const unsigned char PROTOCOL_VERSION = 1;

char packetBuffer[UDP_TX_PACKET_MAX_SIZE + 1];

WiFiUDP Udp;

enum protocol_type_t: char {
    NONE = 0,
    DISCOVERY = 1,
    BROADCAST = 2,
    CONTROL = 3,
    // RESPONSE = 4,
};

enum common_answer_code_t: char {
    OK = 0,
    VERSION_ERROR = 1,
    CRC_ERROR = 2,
    // ENCRYPTION_ERROR = 3, - когда впилю шифрование
    LENGTH_ERROR = 4,
    INVALID_HEADER_ERROR = 5,
    INVALID_PACKET_TYPE = 6,
    OTHER_ERROR = 0xFF,
};

struct protocol_packet_base {
    char protocol_header[3];
    char protocol_version;
    protocol_type_t protocol_type;
};

IPAddress IP_BROADCAST(255, 255, 255, 255);

void sendPacket(protocol_type_t packet_type, char* data, int data_length)
{
    char crc = 0x39;
    Udp.beginPacket(IP_BROADCAST, localPort);
    Udp.write("QLP");
    Udp.write(PROTOCOL_VERSION)
    Udp.write(packet_type)
    Udp.write(data)
    crc ^= packet_type
    for (size_t i = 0; i < data_length; i++)
        crc ^= data[i];
    Udp.write(crc)
    Udp.endPacket();
}

void sendCommonAnswer(protocol_type_t packet_type, common_answer_code_t code, char* data, int data_length)
{
    char crc = 0xA9;
    Udp.beginPacket(IP_BROADCAST, localPort);
    Udp.write("QLP");
    Udp.write(PROTOCOL_VERSION)
    Udp.write(packet_type)
    Udp.write(code)
    Udp.write(data)
    crc ^= packet_type
    for (size_t i = 0; i < data_length; i++)
        crc ^= data[i];
    Udp.write(crc)
    Udp.endPacket();
}

void sendCommonAnswer(protocol_type_t packet_type, common_answer_code_t code)
{
    sendCommonAnswer(packet_type, code, 0, 0);
}

void handle_udp()
{
    // Check has data
    int packetSize = Udp.parsePacket();
    if (!packetSize)
        return;

    // Read
    int n = Udp.read(packetBuffer, UDP_TX_PACKET_MAX_SIZE);
    packetBuffer[n] = 0;

    if (n < 6)
    {
        // Incorrect packet size
        sendCommonAnswer(protocol_type_t::NONE, common_answer_code_t::LENGTH_ERROR);
        return;
    }

    if (strncmp(((protocol_packet_base*)packetBuffer)->protocol_header, "QLP", 3) != 0)
    {
        // Incorrect protocol header
        sendCommonAnswer(protocol_type_t::NONE, common_answer_code_t::INVALID_HEADER_ERROR);
        return;
    }

    protocol_type_t current_packet_type = ((protocol_packet_base*)packetBuffer)->protocol_type;

    if (((protocol_packet_base*)packetBuffer)->protocol_version != PROTOCOL_VERSION)
    {
        // Incorrect version
        sendCommonAnswer(protocol_type_t::NONE, common_answer_code_t::VERSION_ERROR);
        return;
    }

    if ((char)(current_packet_type) > 3)
    {
        // Incorrect protocol type
        sendCommonAnswer(protocol_type_t::NONE, common_answer_code_t::INVALID_PACKET_TYPE);
        return;
    }

    // Calc CRC
    char crc = 0x75;
    for (size_t i = 0; i < n-1; i++)
        crc ^= packetBuffer[i];
    
    if (crc != packetBuffer[n-1])
    {
        // CRC ERROR
        sendCommonAnswer(current_packet_type, common_answer_code_t::CRC_ERROR);
        return;
    }

    if (current_packet_type == protocol_type_t::DISCOVERY)
    {
        if (strncmp(&packetBuffer[sizeof(protocol_packet_base)], "ABH", 3) == 0)
        {
            // Received ABH?
            int uuid = random(0x10000000, 0xFFFFFFFF);
            char buf[3+1+8+1+8+1+1]; // + name
            // %08X\
            sprintf(buf, "IAH-%08X-%08X-", ESP.getChipId(), uuid); // + name
            sendPacket(current_packet_type, buf, strlen(buf));
        }
    }
}

// struct protocol_packet_broadcast
// {
//     char protocol_header[3];
//     protocol_type_t protocol_type;
//     char protocol_version;
//     char group;
//     char command_id;
// };

// struct protocol_packet_control_request
// {
//     char protocol_header[3];
//     protocol_type_t protocol_type;
//     char protocol_version;
//     unsigned int device_id;
//     char command_id;
// };

// struct protocol_packet_control_response
// {
//     char protocol_header[3];
//     protocol_type_t protocol_type;
//     char protocol_version;
//     unsigned int device_id;
//     char control_response;
//     char response_code;
// };

// protocol_packet_base* handle_packet(char* packet) {
//     return (protocol_packet_base*)packet;
// }