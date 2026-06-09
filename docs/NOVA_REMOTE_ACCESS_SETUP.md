# Nova remote PC access setup

## Safe architecture

Use this route:

`phone/laptop -> Tailscale private network -> Remote Desktop or Chrome Remote Desktop -> new PC -> Nova`

Optional advanced route:

`phone/laptop -> Tailscale private network -> token-protected Nova FastAPI bridge`

Do **not** expose Windows Remote Desktop or Nova's API through router port forwarding.

## New PC setup

1. Plug the new PC into Ethernet if possible.
2. Enable Wake-on-LAN / PCIe device wake in BIOS or UEFI.
3. In Windows Device Manager, open the Ethernet adapter, then enable wake options such as allowing the device or magic packet to wake the computer.
4. Install Tailscale on the new PC, phone and laptop, and sign in to the same tailnet.
5. For Windows 11 Pro, enable Settings > System > Remote Desktop. Use the Tailscale IPv4 address when connecting.
6. For Windows Home or easier phone use, set up Chrome Remote Desktop unattended access.

## Nova API setup

Local-only default:

```powershell
.\start_nova_remote_api.ps1
```

Tailscale-only remote API:

```powershell
[Environment]::SetEnvironmentVariable("NOVA_API_TOKEN", "use-a-long-random-token", "User")
# Open a new PowerShell window after setting the User environment variable.
.\start_nova_remote_api.ps1 -HostAddress YOUR_TAILSCALE_IP -Port 8767 -RequireToken
```

Test from the laptop while connected to Tailscale:

```powershell
curl http://YOUR_TAILSCALE_IP:8767/api/v1/health
curl -H "Authorization: Bearer YOUR_TOKEN" http://YOUR_TAILSCALE_IP:8767/api/v1/status
```

## Useful Nova commands

- `/remote-access-plan`
- `/remote-access-status`
- `/remote-access-scripts`
- `/remote-access-test`
- `/remote-api-health YOUR_TAILSCALE_IP 8767 --token YOUR_TOKEN`
- `/remote-profile-wizard --host YOUR_TAILSCALE_IP --mac AA:BB:CC:DD:EE:FF`
- `/remote-profile add newpc --host YOUR_TAILSCALE_IP --port 8767 --mac AA:BB:CC:DD:EE:FF --set-default`
- `/remote-profile validate newpc`
- `/remote-profile health newpc`
- `/remote-profile wake newpc --dry-run`
- `/remote-profile wake newpc --confirm`
- `/remote-wake AA:BB:CC:DD:EE:FF --dry-run`
- `/remote-wake AA:BB:CC:DD:EE:FF --confirm`

## Troubleshooting

- Wake-on-LAN usually works best over Ethernet and from sleep/hibernate, not after a full shutdown on every motherboard.
- If RDP connects on LAN but not away from home, use Tailscale and connect to the Tailscale IPv4, not your public IP.
- If Nova API is remote, set `NOVA_API_TOKEN` and bind to the Tailscale IP only.
- If Windows sleeps too aggressively, adjust power settings so the network adapter can wake the PC.
