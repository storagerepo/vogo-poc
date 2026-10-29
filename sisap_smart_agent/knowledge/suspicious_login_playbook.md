# Suspicious login playbook

## Triggers
Failed login followed by a success, login from a new IP or country, logins from two countries within a short time (impossible travel), and logins without a recorded MFA result.

## Check 1: failed then successful login
A failed login followed by a successful one from the same IP can be a mistyped password or a successful password-guessing attempt. It does not prove compromise on its own. Compare the source IP with the user's known IPs and check whether MFA was completed.

## Check 2: new IP or country
Compare the source IP and country with the user's baseline. A known IP is conflicting evidence; an unknown IP in a different country is supporting evidence.

## Check 3: impossible travel
Two successful logins from distant countries within minutes suggest either a VPN or proxy, or a stolen session or credentials. Check whether either IP belongs to a corporate VPN.

## Check 4: privileged accounts
Any role assignment or privilege change soon after a suspicious login is high risk. Treat it as Critical and recommend immediate human review.

## Check 5: MFA
If the MFA result is missing for a successful login, note it as missing evidence and recommend retrieving MFA provider logs.

## Recommended next checks
Confirm with the account owner using a verified channel, review other accounts targeted from the same source IP, review endpoint events on the user's device, and let a human analyst decide on containment such as password reset or session revocation.
