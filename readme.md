# Remote device management tools

A local network device management system built using FastAPI, React, and Rust.

Currently only sends Wake-on-LAN packets, though I'd love to add more features in the future.

My personal use case is to wake up my home server when I'm away from home (or even just in another room).  I run the web frontend on a Raspberry Pi and the listener on my server.  Both are connected to the same Tailscale network, so I can access the web frontend from anywhere.

## Overview

This system is composed of four main components:

FastAPI server: Serves the API for serving device information and sending Wake-on-LAN requests.
React frontend: A user interface for displaying the list of devices and triggering Wake-on-LAN requests.
Rust listener: Listens for multicast messages and updates the SQLite database with device information.
Rust sender: Sends multicast messages with device information (IP, MAC, and hostname) at a regular interval.

```mermaid
sequenceDiagram
    participant UI as User Interface
    participant API as FastAPI Server
    participant DB as SQLite Database
    participant Listener as Rust Listener
    participant Sender as Rust Sender (remote device)

    UI->>UI: Periodic refresh (1 minute)
    UI->>API: GET /devices
    API->>DB: SELECT * FROM devices
    DB-->>API: List of devices
    API-->>UI: JSON devices list

    UI->>UI: Click "Wake On LAN" button
    UI->>API: POST /wake-on-lan (MAC address)
    API->>API: Send Wake-on-LAN packet
    API-->>UI: Wake-on-LAN status

    Sender->>Listener: Multicast message (IP, MAC, Hostname)
    Listener->>DB: Update device info in database
    DB-->>Listener: Update confirmation
```