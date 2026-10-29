# Firewall troubleshooting guide

## Principles
Never disable a firewall to test connectivity, and never change firewall rules without an approved change request. Support agents can only run read-only checks and recommend that an engineer reviews rules.

## Application cannot reach a service
Identify the destination host, port and protocol. Run a port check against the allow-listed target. A result of "filtered" means a firewall is silently dropping traffic; "closed" means the host answered but nothing is listening. If the port is filtered, collect the source IP and time and escalate to the network engineering team to review the rule.

## Local device firewall
On Windows, check that the application is allowed under Windows Defender Firewall inbound and outbound rules. Third-party security suites may have their own firewall; check whether the VPN client or application is blocked there. Do not disable the firewall; ask the user to review the blocked-connections log instead.

## Router or home network blocks
Many consumer routers block IPsec or non-standard UDP ports. Ask the user to enable VPN or IPsec pass-through, or test using a mobile hotspot to confirm that the home network is the cause.

## Evidence to include in a ticket
Source device and network, destination host and port, protocol, exact time of the failure, result of the port check and any firewall log entry the user can see.
