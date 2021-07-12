# SCHC over Sifgox for LoPy4

## User guide

To run the code on the LoPy4, create a folder named `stats` with an empty file. The code will use these
folders to store data from experiments. 

After that, upload the code to the LoPy4. The `main.py` script will automatically be executed in the device, using the
configurations from `config.py`. This will generate JSON files in the `stats` folder, which can be moved towards a new
`results` folder.

The `main.py` script instantiates a `SCHCSender` for each transmission, sending fragments using methods from that
object.

After running a set of experiments, the script `extract_data.py` can be run in order to process data from `results`.

## Directories

This project consists on the following directories.

### Entities

Here are the Python classes that define de Sigfox SCHC profile (`SigfoxProfile(Protocol)`) as well as additional objects
to be instantiated in every SCHC transmission. The `exceptions` file defines a set of specific exceptions that can be caught.

* `Fragmenter` performs the fragmentation of a SCHC Packet.
* `Reassembler` merges a list of SCHC Fragments into the original SCHC Packet.
* `SCHCTimer` implements a timer meant to be used to wait during certain periods of time and debugging.
* `SCHCLogger` implements a logging object that keeps track of many variables of a SCHC transmission.
* `SCHCSender` is the class transmits the SCHC Fragments to the Sigfox network.

### Messages

This directory contains classes for the messages and headers in a SCHC transmission.

* `Fragment` contains parameters and methods for an individual fragment.
  * `FragmentHeader` comprises the header of a fragment.
* `ACK` contains parameters and methods for an individual SCHC ACK.
  * `ACKHeader` comprises the header of a SCHC ACK.
* `Header` is the generalization of both types of headers.
* `SenderAbort` is an extension of `Fragment`, used to abort the transmission from the sender side.
* `ReceiverAbort` is an extension of `ACK`, used to abort the transmission from the receiver side.

### Packets

This directory contains data up to a certain amount of bytes, meant to be used in transmissions as SCHC Packets.

### Testing

This folder contains scripts that serve particular purposes, used to test connectivity, send individual messages, etc. 
The `unit_tests.py` script runs unit tests for many methods and functions of the classes,
as well as checking their format.

## Dependencies

This code is to be run in a Pycom LoPy4, which uses Micropython as programming language with additional modules and
dependencies defined exclusively for Pycom devices. Please check
[the Pycom documentation](https://docs.pycom.io/firmwareapi/) for more information regarding these modules.

## Authors

This code was developed by the following people, with the aid of the
[SCHC over Sigfox draft](https://datatracker.ietf.org/doc/html/draft-ietf-lpwan-schc-over-sigfox) authors.
* Diego Wistuba
* Sergio Aguilar
* Antonis Platis
