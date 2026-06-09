# Phone access to Nova with LAN or Tailscale

This is a safe access checklist for using Nova from your phone while Nova runs on your Windows PC.

## Start Nova on the PC

From the extracted Nova folder, start the web UI in the normal way:

```powershell
python app.py --web --host 0.0.0.0 --port 8766
```

Use `127.0.0.1` only when accessing Nova from the same PC. Use `0.0.0.0` when another device, such as your phone, needs to reach the server.

## Phone address on the same Wi-Fi

Find the PC's LAN IP address:

```powershell
ipconfig
```

Look for the IPv4 address on your active Wi-Fi/Ethernet adapter, then open this on your phone:

```text
http://PC_LAN_IP:8766
```

Example shape:

```text
http://192.168.1.25:8766
```

## Phone address with Tailscale

1. Install and sign into Tailscale on the PC.
2. Install and sign into Tailscale on the phone with the same tailnet.
3. In the Tailscale app, copy the PC's Tailscale IP address or MagicDNS name.
4. Start Nova on the PC with `--host 0.0.0.0`.
5. Open this on the phone:

```text
http://PC_TAILSCALE_IP:8766
```

or, if MagicDNS is enabled:

```text
http://PC_NAME:8766
```

## Windows firewall fixes

If the page does not load:

- Confirm Nova is running on the PC.
- Confirm the command used `--host 0.0.0.0`, not only `127.0.0.1`.
- Allow Python through Windows Defender Firewall on Private networks.
- Keep Nova on a private trusted network or Tailscale, not the open internet.
- Try temporarily changing the port if another app is using `8766`.

## Confirm Nova is reachable

From the PC:

```powershell
curl http://127.0.0.1:8766
```

From another device on the same network or Tailscale:

```text
http://PC_IP_OR_TAILSCALE_NAME:8766
```

If the PC works locally but the phone cannot connect, the issue is usually firewall, wrong IP address, wrong host binding, or the phone not being on the same LAN/Tailscale network.

## Safety notes

Do not port-forward Nova to the public internet unless you have added proper authentication and understand the risk. Tailscale is safer because it limits access to your private tailnet.
