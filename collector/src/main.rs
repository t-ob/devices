use byteorder::{NetworkEndian, ReadBytesExt};
use rusqlite::{Connection, Result};
use std::io::{Cursor, Read};
use std::net::{IpAddr, Ipv4Addr, SocketAddr, UdpSocket};

fn main() -> Result<()> {
    let matches = clap::App::new("collector")
        .arg(
            clap::Arg::with_name("database")
                .required(true)
                .short('d')
                .long("database")
                .value_name("FILE")
                .help("Sets the database file to use")
                .takes_value(true),
        )
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
            clap::Arg::with_name("multicast_interface")
                .required(true)
                .short('i')
                .long("multicast_interface")
                .value_name("IP")
                .help("Sets the multicast interface to listen on")
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
        .arg(
            clap::Arg::with_name("port")
                .required(true)
                .short('p')
                .long("port")
                .value_name("PORT")
                .help("Sets the port to listen on")
                .takes_value(true),
        )
        .get_matches();

    let database = matches.value_of("database").unwrap();
    // Set up the SQLite database
    let conn = Connection::open(database)?;
    conn.execute(
        "CREATE TABLE IF NOT EXISTS devices (
            id          INTEGER PRIMARY KEY,
            ip_address  TEXT NOT NULL,
            mac_address TEXT NOT NULL UNIQUE,
            hostname    TEXT NOT NULL,
            last_seen   TEXT NOT NULL
        )",
        [],
    )?;

    // Listen for multicast messages
    let multicast_group = matches
        .value_of("multicast_group")
        .unwrap()
        .parse::<Ipv4Addr>()
        .unwrap();
    let multicast_interface = matches
        .value_of("multicast_interface")
        .unwrap()
        .parse::<Ipv4Addr>()
        .unwrap();

    let local_addr = SocketAddr::new(
        matches.value_of("bind").unwrap().parse::<IpAddr>().unwrap(),
        matches.value_of("port").unwrap().parse::<u16>().unwrap(),
    );
    let socket = UdpSocket::bind(local_addr).expect("Couldn't bind socket");

    socket
        .join_multicast_v4(&multicast_group, &multicast_interface)
        .expect("join_multicast_v4 failed");

    let mut buffer = [0; 1024];

    loop {
        let (num_bytes, _) = socket.recv_from(&mut buffer).expect("recv_from failed");
        let mut cursor = Cursor::new(&buffer[..num_bytes]);

        let ip_length = cursor.read_u32::<NetworkEndian>().unwrap() as usize;
        let mut ip_address = vec![0; ip_length];
        cursor.read_exact(&mut ip_address).unwrap();

        let mac_length = cursor.read_u32::<NetworkEndian>().unwrap() as usize;
        let mut mac_address = vec![0; mac_length];
        cursor.read_exact(&mut mac_address).unwrap();

        let hostname_length = cursor.read_u32::<NetworkEndian>().unwrap() as usize;
        let mut hostname = vec![0; hostname_length];
        cursor.read_exact(&mut hostname).unwrap();

        let ip_address = String::from_utf8(ip_address).expect("Invalid UTF-8 string");
        let mac_address = String::from_utf8(mac_address).expect("Invalid UTF-8 string");
        let hostname = String::from_utf8(hostname).expect("Invalid UTF-8 string");

        println!(
            "Received message: IP: {}, MAC: {}, Hostname: {}",
            ip_address, mac_address, hostname
        );

        // Update the SQLite database
        conn.execute(
            "INSERT OR REPLACE INTO devices (id, ip_address, mac_address, hostname, last_seen)
             VALUES (
                (SELECT id FROM devices WHERE mac_address = ?1),
                ?1, ?2, ?3, datetime('now')
             )",
            &[&ip_address, &mac_address, &hostname],
        )?;
    }
}
