# Simulate Dji RC231 as a game controller

<img height="400" src="DJI-RC-N1-Remote-Controller.png" width="400"/>

## How to using

### 1. Install vJoy

This requires vJoy. Please download and install from below.

https://sourceforge.net/projects/vjoystick/

### 2. Install Python

```powershell
PS D:/Desktop> python --version
Python 3.10.11
PS D:/Desktop> pip install -r requirements.txt
...
PS D:/Desktop> pip ilst 
Package    Version
---------- -------
pip        23.3.1
pyserial   3.5
pyvjoy     1.0.1
setuptools 65.5.0
```

### 3. Clone this repository

```bash
git clone https://github.com/Limitex/DJI-RC201-Simulator-for-vJoy
cd DJI-RC201-Simulator-for-vJoy
```

### 4. Run

```bash
python main.py
```