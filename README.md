# Telelumen-Wrapper

A Python wrapper designed to facilitate the connection and use of Telelumen booth lighting systems.

## Overview

This wrapper simplifies interactions with Telelumen luminaires by providing easy-to-use connection methods and utility functions. It abstracts the complexity of the underlying `api_tng` module, making it straightforward to discover, connect to, and control Telelumen lighting devices.

## Features

- **Easy Discovery**: Automatically discover all Telelumen luminaires on the network
- **Multiple Connection Methods**: Connect by index selection, IP address, or serial number
- **Batch Operations**: Connect to multiple luminaires simultaneously
- **Simple Disconnect**: Clean disconnection handling for single or multiple devices

## Connection Methods

1. **Interactive List Selection**: Display all available luminaires and choose by index or connect to all
2. **Direct IP Connection**: Connect directly using a luminaire's IP address
3. **Serial Number Connection**: Find and connect to a specific luminaire by its serial number

## Requirements

- Python 3.12
- `api_tng` module (Telelumen API)
- packages in `requirements.txt`
