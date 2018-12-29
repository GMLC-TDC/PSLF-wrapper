# PSLF_wrapper
Wrapper for PLSF

# Introduction

Positive Sequence Load Flow (PSLF) developed by GE is a widely used commercial tool for transmission level power system analysis by many power utilities and ISOs. Integration of PSLF with HELICS provides us with transmission level power flow, optimal power flow, and dynamic simulation capabilities.

GE currently supports the following features through it's python interface:
* Interface for power flow and dynamic data querying and modification.
* Interface for power flow calculation.
* Interface for basic dynamic simulation. 

Currently not supported (on GE’s to do list)
* Optimal Power Flow and LMP calculation.
* Load changing at each time step of the dynamic simulation.

Hence PSLF wrapper implementation supports only steady flow simulation. Dynamic power flow simulation will be integrated when the necessary API's are ready.

# Installation Instructions

PSLF tool is supported only in Windows so will need to install HELICS on Windows as well. For steady state power flow simulation we will also need GridLAB-D for distribution side simulation. The instructions that follow are for multi-machine, multi-OS simulation setup where PSLF integrated with HELICS runs on a Windows machine and GridLAB-D integrated with HELICS runs on a linux machine.

## PSLF installation
  **1. Install licensed version of PSLF on Windows
  **2. Download the PLSF-HELICS integrated code.
  ```sh
        git clone https://github.com/GMLC-TDC/PSLF-wrapper.git
  ```

## HELICS installation on Windows

Follow the instructions for HELICS installation on Windows https://gmlc-tdc.github.io/HELICS-src/installation/windows.html. In addition to this, here are some additional steps that we need to take care of for PSLF integration. PSLF works with 32 bit version of python so we need to ensure that Miscrosoft Visual Studio, boost libraries, and python are 32 bit versions. 

**1. Install Boost Pre-built library 1.66 (32 version) needed by HELICS. Pre-built libraries are available in  https://dl.bintray.com/boostorg/release/1.66.0/binaries/. Please make sure “BOOST_INSTALL_PATH” environment variable is set to install location.

* Install miniconda for python and swig packages. Download from https://repo.continuum.io/miniconda/. Select the option : "add to PATH env" so that installation path gets added to "PATH" enviroment variable. Next step is to install swig through miniconda. 
```sh
    conda install swig
```

**2. Download HELICS source code git clone https://github.com/GMLC-TDV/HELICS-src.git. We will have to build HELICS with python 2.7 support. Open "x86 Native Tools Command Prompt VS 2017" command prompt fron Windows start menu.

```sh
    cd HELICS-src
    mkdir build
    cd build
    cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="C:\local\helics-v1.3.0" -	DBOOST_ROOT="C:\local\boost_1_66_1" -DBUILD_PYTHON2_INTERFACE=ON -G "Visual Studio 15 2017" ..
    cmake --build . --config Release --target install
```

## HELICS installation on Linux

Please follow instructions in https://gmlc-tdc.github.io/HELICS-src/installation/linux.html to install HELICS on Linux. Add additional CMAKE flag during the configuration step.

```sh
    CMAKE_CXX_FLAGS = -fPIC -std=c++14
```

## GridLAB-D installation on Linux

**1. Please download GridLABD.
    ```sh
        git clone -b feature/1024 http://github.com/gridlab-d/gridlab-d.git
    ```
**2. Build/install third party prerequisites: xerces-c, automake, libtool
**3. Build GridLAB-D:
    ```sh
        autoreconf -if
        ./configure --prefix=<install path> --with-helics=<helics install path> --enable-silent-rules ‘CFLAGS=-g -O0 -w’ ‘CXXFLAGS=-g -O0 -w -std=c++14’ ‘LDFLAGS=-g -O0 -w’
        make
        make install
    ```

PSLF<->HELICS<->GridLAB-D Setup

PSLF integrated with HELICS should run on the Windows machine and HELICS broker and GridLAB-D integrated with HELICS should run on the Linux machine.

<<image>>

If the windows machine is behind a firewall, then we need to open port range (23400 – 23700) to enable incoming traffic from Linux machine. 

**1. Add inbound rule for port range 23400 - 23700 on your windows machine
    a. Go to Control Panel->Windows Firewall ->Advanced settings ->Inbound Rules->New Rule
    b. Set Protocol type as TCP
    c. Set port range as 23400 – 23700
    d. Call IT helpdesk to open port range
    e. Restart computer for the changes get reflected

**2. On the Windows machine, traverse to PSLF wrapper directory. Update the broker address and PSLF federate address in pslf_helics_config.json config file.

**3. Start PSLF-HELICS integrated steady state simulation code
    ```sh
        python pslf_wrapper.py
    ```

**4. Start HELICS broker on Linux machine
    ```sh
        helics_broker 2 --log-level=3 --name=mainbroker --interface=tcp://<local IP>:23404
    ```

**5. We need to ensure that GridLabD and PSLF connect to the same broker IP and port number. Core init string parameter for federate
	```sh
        “--federates=1 --broker_address=tcp://<broker ip> --interface=tcp://<local ip>”
    ```








