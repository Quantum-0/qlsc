#include <WiFiUdp.h>

const unsigned int localPort = 52075;
const unsigned char PROTOCOL_VERSION = 1;

char packetBuffer[UDP_TX_PACKET_MAX_SIZE + 1];

WiFiUDP Udp;

enum class protocol_type_t: char {
    NONE = 0,
    DISCOVERY = 1,
    BROADCAST = 2,
    CONTROL = 3,
    // RESPONSE = 4,
};

enum class common_answer_code_t: char {
    OK = 0,
    VERSION_ERROR = 1,
    CRC_ERROR = 2,
    // ENCRYPTION_ERROR = 3, - когда впилю шифрование
    LENGTH_ERROR = 4,
    INVALID_HEADER_ERROR = 5,
    INVALID_PACKET_TYPE = 6,
    OTHER_ERROR = 0xFF,
};

#pragma pack(push, 1)
struct protocol_packet_base {
    char protocol_header[3];
    char protocol_version;
    protocol_type_t protocol_type;
};


struct protocol_packet_control {
    char protocol_header[3];
    char protocol_version;
    protocol_type_t protocol_type;
    unsigned long device_id;
    unsigned char command_id;
};
#pragma pack(pop)

IPAddress IP_BROADCAST(255, 255, 255, 255);

void sendPacket(protocol_type_t packet_type, char* data, size_t data_length)
{
    char crc = 0x39;
    Udp.beginPacket(IP_BROADCAST, localPort);
    Udp.write("QLP");
    Udp.write(PROTOCOL_VERSION);
    Udp.write((char)packet_type);
    Udp.write(data);
    crc ^= (char)packet_type;
    for (size_t i = 0; i < data_length; i++)
        crc ^= data[i];
    Udp.write(crc);
    Udp.endPacket();
}

void sendCommonAnswer(protocol_type_t packet_type, common_answer_code_t code, char* data, size_t data_length)
{
    char crc = 0xA9;
    Udp.beginPacket(IP_BROADCAST, localPort);
    Udp.write("QLP");
    Udp.write(PROTOCOL_VERSION);
    Udp.write((char)packet_type);
    Udp.write((char)code);
    Udp.write(data);
    crc ^= (char)packet_type;
    for (size_t i = 0; i < data_length; i++)
        crc ^= data[i];
    Udp.write(crc);
    Udp.endPacket();
}

void sendCommonAnswer(protocol_type_t packet_type, common_answer_code_t code)
{
    sendCommonAnswer(packet_type, code, 0, 0);
}

void handle_udp()
{
    // Check has data
    size_t packetSize = Udp.parsePacket();
    if (!packetSize)
        return;

    // Read
    size_t n = Udp.read(packetBuffer, UDP_TX_PACKET_MAX_SIZE);
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
            int uuid = random(0xFFFFFFFF);
            char buf[256];
            sprintf(buf, "IAH-%08X-%08X-%s", ESP.getChipId(), uuid, "My Favorite Device");
            sendPacket(current_packet_type, buf, strlen(buf));
        }
    }

    if (current_packet_type == protocol_type_t::CONTROL)
    {
        // Replace with uuid later
        if (((protocol_packet_control*)packetBuffer)->device_id != ESP.getChipId())
            return;

        unsigned char command_id = ((protocol_packet_control*)packetBuffer)->command_id;
        unsigned char* data_ptr = (unsigned char*)packetBuffer+sizeof(protocol_packet_control);
        unsigned int data_len = n - sizeof(protocol_packet_control) - 1; // header and crc

        if (command_id == 0x74)
        {
            sendCommonAnswer(protocol_type_t::CONTROL, common_answer_code_t::OK);
            strip.fill(0);
            strip.show();
            ESP.reset();
        }
        if (command_id == 0x01)
        {
            if (data_len == 1)
            {
                strip.fill(0);
                strip.updateLength(data_ptr[0]); // TODO: must be 2 bytes
                strip.setPixelColor(data_ptr[0]-1, 0x0000FF);
                strip.show(); // HERE FOR TEST
                sendCommonAnswer(protocol_type_t::CONTROL, common_answer_code_t::OK);
            }
            else
                sendCommonAnswer(protocol_type_t::CONTROL, common_answer_code_t::LENGTH_ERROR);
        }
        if (command_id == 0x54)
        {
            if (data_len == 3)
            {
                unsigned long color = (data_ptr[0] << 16) | (data_ptr[1] << 8) | data_ptr[2];
                strip.fill(color);
                strip.show(); // HERE FOR TEST
                sendCommonAnswer(protocol_type_t::CONTROL, common_answer_code_t::OK);
            }
            else
                sendCommonAnswer(protocol_type_t::CONTROL, common_answer_code_t::LENGTH_ERROR);
        }
        if (command_id == 0x51)
        {
            if (data_len == 5)
            {
                unsigned int index = *((unsigned int*)data_ptr);
                unsigned long color = (data_ptr[2] << 16) | (data_ptr[3] << 8) | data_ptr[4];
                strip.setPixelColor(index, color);
                strip.show(); // HERE FOR TEST
                sendCommonAnswer(protocol_type_t::CONTROL, common_answer_code_t::OK);
            }
            else
                sendCommonAnswer(protocol_type_t::CONTROL, common_answer_code_t::LENGTH_ERROR);
        }
        if (command_id == 0x52)
        {
            if (data_len == 7)
            {
                unsigned int index1 = *((unsigned int*)data_ptr);
                unsigned int index2 = *((unsigned int*)(data_ptr+2));
                unsigned long color = (data_ptr[4] << 16) | (data_ptr[5] << 8) | data_ptr[6];
                for (size_t i = index1; i < index2; i++)
                {
                    strip.setPixelColor(i, color);
                }
                strip.show(); // HERE FOR TEST
                sendCommonAnswer(protocol_type_t::CONTROL, common_answer_code_t::OK);
            }
            else
                sendCommonAnswer(protocol_type_t::CONTROL, common_answer_code_t::LENGTH_ERROR);
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