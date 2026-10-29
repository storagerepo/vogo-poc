# Network troubleshooting guide

## Connectivity basics
Check the physical layer first: Wi-Fi connected, cable plugged in, airplane mode off. Test a public website and an internal portal separately. If only internal resources fail, the issue is likely VPN, DNS or routing rather than the internet link.

## DNS problems
Symptoms: the browser shows a name-not-resolved error but the IP address works. Steps: flush the local DNS cache, confirm the device uses the company DNS servers when connected to VPN, and run a DNS resolution check for the failing name. If an internal name returns NXDOMAIN while public names work, the internal DNS record or the split-DNS configuration needs engineer attention.

## High latency or packet loss
Run a connectivity check to the gateway and to a public address. If the gateway shows loss but the public address does not, the problem is on the local or corporate segment. Test on a wired connection and move closer to the Wi-Fi access point.

## Wi-Fi drops
Forget and rejoin the network, update the Wi-Fi driver, and check whether the problem happens only in one room or at one time of day. Repeated drops across several users should be reported to the network team.

## Proxy and captive portals
If a page never loads on hotel or guest Wi-Fi, open a plain http site to trigger the captive portal sign-in. Remove any stale proxy settings left from another network.
