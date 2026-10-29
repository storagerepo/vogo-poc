# VPN troubleshooting guide

## Before you start: safe checks
Collect the device type, operating system, VPN client name, exact error text and what has already been tried. Only safe, read-only checks are allowed: connectivity to the VPN gateway, VPN service status, DNS resolution and port reachability. Never ask a user to share a password, token or MFA code.

## Error: connection timed out
A timeout usually means the VPN tunnel traffic is not reaching the gateway. Step 1: confirm the device has normal internet access by opening a public website. Step 2: disconnect and reconnect the VPN client. Step 3: switch networks, for example from home Wi-Fi to a mobile hotspot; if it works on the hotspot, the home router or ISP is blocking VPN traffic. Step 4: run the gateway connectivity and port checks (UDP 500, UDP 4500, TCP 443). If UDP 4500 is filtered, the local firewall or router is dropping IPsec NAT-T traffic.

## Error: authentication failed
Check that the username is typed correctly and that the account is not locked. Confirm the MFA prompt was approved on the registered device and that the phone clock is set automatically. If the password was changed recently, sign out of the VPN client and sign in again. After three failed attempts the account may lock; do not keep retrying, create a ticket instead.

## Error 809 or tunnel handshake failure
This error normally means IPsec ports are blocked. Ask the user to check that no third-party firewall or security suite is blocking UDP 500 and UDP 4500, and that the router has IPsec or VPN pass-through enabled. On Windows, confirm the VPN client service is running and restart it if it is stopped.

## Certificate or time errors
If the client reports an untrusted certificate or expired session, check that the device date, time and time zone are correct and synchronized. A wrong clock is a common cause of certificate errors.

## Slow VPN after connecting
Disconnect heavy uploads or video calls and test again. Check whether split tunneling is enabled according to company policy. If latency to the gateway is above 150 ms, try a different gateway region.

## When to escalate
Escalate to an engineer when the gateway checks fail from more than one network, when the account is locked, when the error is unfamiliar, or when the user has completed all steps in this guide and the problem remains.
