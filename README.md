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

## Ultralytics

### Warning

Raspberry Pi 4 comes with Python 3.13 where the minimum PyTorch version available is v2.6. 
This conflicts with Ultralytics Python package. Torch must be downgraded to be v2.5.1 for 
Ultralytics to work. This means Python will need to be downgraded as well. This repo is
using Python 3.11 -- installed via pyenv.


