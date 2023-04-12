use byteorder::{NetworkEndian, WriteBytesExt};
use std::net::{IpAddr, SocketAddr, UdpSocket};
use std::thread;
use std::time::Duration;

fn main() {
    let matches = clap::App::new("agent")
        .arg(
            clap::Arg::with_name("multicast_group")
                .required(true)
                .short('m')
                .long("multicast_group")
                .value_name("IP")
                .help("Sets the multicast group to listen on")
                .takes_value(true),
        )
        .arg(
            clap::Arg::with_name("multicast_port")
                .required(true)
                .short('p')
                .long("multicast_port")
                .value_name("PORT")
                .help("Sets the multicast port to listen on")
                .takes_value(true),
        )
        .arg(
            clap::Arg::with_name("bind")
                .required(true)
                .short('b')
                .long("bind")
                .value_name("IP")
                .help("Sets the IP address to bind to")
                .takes_value(true),
        )
        .get_matches();
    // Get the IP address, MAC address, and hostname
    let iface = pnet::datalink::interfaces()
        .into_iter()
        .find(|iface| iface.is_up() && !iface.is_loopback() && !iface.ips.is_empty())
        .expect("No suitable network interface found.");

    let ip_address = iface.ips[0].ip().to_string();
    let mac_address = iface
        .mac
        .expect("No MAC address found for interface.")
        .to_string();
    let hostname = hostname::get()
        .expect("Could not get hostname for device.")
        .into_string()
        .unwrap();

    // Construct the message
    let mut message = Vec::new();
    message
        .write_u32::<NetworkEndian>(ip_address.len() as u32)
        .unwrap();
    message.extend_from_slice(ip_address.as_bytes());
    message
        .write_u32::<NetworkEndian>(mac_address.len() as u32)
        .unwrap();
    message.extend_from_slice(mac_address.as_bytes());
    message
        .write_u32::<NetworkEndian>(hostname.len() as u32)
        .unwrap();
    message.extend_from_slice(hostname.as_bytes());

    // Create the socket
    let local_addr = SocketAddr::new(
        matches.value_of("bind").unwrap().parse::<IpAddr>().unwrap(),
        0,
    );

    let socket = UdpSocket::bind(local_addr).unwrap();

    // Set the time-to-live for the message
    socket.set_multicast_ttl_v4(1).unwrap();

    // let multicast_group = SocketAddr::new(IpAddr::V4(Ipv4Addr::new(224, 1, 1, 1)), 5007);
    let multicast_group = SocketAddr::new(
        matches
            .value_of("multicast_group")
            .unwrap()
            .parse::<IpAddr>()
            .unwrap(),
        matches
            .value_of("multicast_port")
            .unwrap()
            .parse::<u16>()
            .unwrap(),
    );

    loop {
        // Send the data
        socket
            .send_to(&message, &multicast_group)
            .expect("Could not send data.");

        // Sleep for 60 seconds
        thread::sleep(Duration::from_secs(60));
    }
}
