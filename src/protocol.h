#include <WiFiUdp.h>

const unsigned int localPort = 52075;
const unsigned char PROTOCOL_VERSION = 1;

char packetBuffer[UDP_TX_PACKET_MAX_SIZE + 1];

WiFiUDP Udp;

enum protocol_type_t: char {
    DISCOVERY = 1,
    BROADCAST = 2,
    CONTROL = 3,
    // RESPONSE = 4,
};

struct protocol_packet_base {
    char protocol_header[3];
    char protocol_version;
    protocol_type_t protocol_type;
};

IPAddress IP_BROADCAST(255, 255, 255, 255);

void string2hexString(char* input, char* output)
{
    int loop;
    int i; 
    
    i=0;
    loop=0;
    
    while(input[loop] != '\0')
    {
        sprintf((char*)(output+i),"%02X", input[loop]);
        loop+=1;
        i+=2;
    }
    //insert NULL at the end of the output string
    output[i++] = '\0';
}

void handle_udp()
{
    // Check has data
    int packetSize = Udp.parsePacket();
    if (!packetSize)
        return;

    strip.setPixelColor(0, 0x111111);
    strip.show();
    delay(2000);
    
    Udp.beginPacket(IP_BROADCAST, localPort);
    Udp.write("recv123");
    Udp.endPacket();

    // Read
    int n = Udp.read(packetBuffer, UDP_TX_PACKET_MAX_SIZE);
    packetBuffer[n] = 0;

    Udp.beginPacket(IP_BROADCAST, localPort);
    Udp.write(packetBuffer);
    char packetBufferX2[packetSize*2+1];
    string2hexString(packetBuffer, packetBufferX2);
    Udp.write(packetBufferX2);
    Udp.endPacket();

    if (n < 6)
    {
        // Incorrect packet size
        Udp.beginPacket(IP_BROADCAST, localPort);
        Udp.write("incorrect size");
        Udp.endPacket();
        return;
    }

    if (strncmp(((protocol_packet_base*)packetBuffer)->protocol_header, "QLP", 3) != 0)
    {
        // Incorrect protocol header
        Udp.beginPacket(IP_BROADCAST, localPort);
        Udp.write("incorrect header");
        Udp.endPacket();
        return;
    }

    protocol_type_t current_packet_type = ((protocol_packet_base*)packetBuffer)->protocol_type;

    if ((char)(current_packet_type) > 3)
    {
        // Incorrect protocol type
        Udp.beginPacket(IP_BROADCAST, localPort);
        Udp.write("incorrect proto type");
        Udp.endPacket();
        return;
    }

    if (((protocol_packet_base*)packetBuffer)->protocol_version != PROTOCOL_VERSION)
    {
        // Incorrect version
        Udp.beginPacket(IP_BROADCAST, localPort);
        Udp.write("incorrect ver");
        Udp.endPacket();
        return;
    }

    // Calc CRC
    char crc = 0x75;
    for (size_t i = 0; i < n-1; i++)
        crc ^= packetBuffer[i];
    
    if (crc != packetBuffer[n-1])
    {
        // CRC ERROR
        Udp.beginPacket(IP_BROADCAST, localPort);
        Udp.write("incorrect crc\nMust be = ");
        char str[5];
        sprintf(str, "%d", crc);
        Udp.write(str);
        Udp.endPacket();
        return;
    }

    if (current_packet_type == protocol_type_t::DISCOVERY)
    {
        if (strncmp(&packetBuffer[sizeof(protocol_packet_base)], "ABH", 3) == 0)  // QLP\x01\x01ABH\x41
        {
            // Received ABH?
            Udp.beginPacket(IP_BROADCAST, localPort);
            Udp.write("QLP\x01\x01IAH");
            Udp.endPacket();
        }
        Udp.beginPacket(IP_BROADCAST, localPort);
        Udp.write("Nope");
        Udp.endPacket();
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