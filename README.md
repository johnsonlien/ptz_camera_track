# Tracking PTZ Camera

Create a PTZ camera that can track and move on a Raspberry Pi

Setup:

- Typical USB webcam
- Raspberry Pi 4 w 4 GB ram
- Survos


# Environment

## WSL

If using a WSL environment, the webcam must be mounted in WSL.

1. Install usbipd-win on Windows
    - Powershell (admin): `winget install uspipd-win` 
2. Install v4l2 on Windows
    - Powershell (admin): `winget install v4l2`
3. List usb devices to get Bus ID of device
    - Powershell (user): `usbipd list`

```bash
> usbipd list
Connected:
BUSID   VID:PID Device              State
1-5     ...:... USB Live Camera     Not shared
```

4. Bind USB Device
    - Powershell (user): `uspipd bind --busid <BUSID>`
5. Attach camera to WSL
    - Powershell (user): `uspipd attach --wsl --busid <BUSID>`

```bash
> usbipd list
Connected:
BUSID   VID:PID Device              State
1-5     ...:... USB Live Camera     Attached 
```

6. Update permissions on WSL to access camera
    - `sudo chmod 666 /dev/video*`

