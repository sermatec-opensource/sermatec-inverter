# Development guide
This guide aims to demonstrate a basic reverse-engineering workflow.

## Requirements
- An Android smartphone or tablet that has been rooted and has the tcpdump and Sermatec apps installed,
- adb,
- Wireshark,
- A hex editor (optional for faster data inspection).
- Sermatec inverter (obviously).

## Workflow
### Preparation
Firstly, you will need to root your Android device. Without root, you won't be able to access the adb shell with the required privileges. After that, allow debugging and adb root access in the developer options. Don't forget that the options are usually hidden and you need to enable them (usually by tapping the build number in the `About phone` menu several times; consult your Android version manual).

![ADB in the Developer Options](../assets/adb.png)

Now you should be able to start an adb session in your computer's terminal as root: `adb root`.

### Getting the Data
We will dump the devices' traffic with tcpdump and pipe it to the computer's Wireshark.

Open the terminal and prepare the following command: `adb shell "tcpdump -vv -i any -Uw - 2>/dev/null" | wireshark -kSi -`. 
Note: You need to have `tcpdump` and `adb` included in your $PATH, or use the full path to the respective executables instead.

When you are ready, execute the command, open the Sermatec app, and select a Local Connection Mode. Connect to the inverter, pick a section you want to decode in the protocol, and expand the section. Take a screenshot and stop the capture in Wireshark. Now it's time to inspect the captured packets and compare the data to the values in the screenshot.

### Inspection
Now we have a couple of packets. To eliminate irrelevant ones, use this Wireshark filter: `ip.addr == 10.10.100.254 && tcp.flags.push == 1`. Inverter's default IP in the Local Connection Mode is `10.10.100.254`. This could be verified in the UART-TCP module settings available at the inverter's LAN IP at port 80. Check out the README.md for more information.

After filtering out the irrelevant packets, we can search for our values. Because the structure of the protocol is already known, it is easy to find packets containing new commands (and responses). For example, I chose the command `0x000d`, found the response (source is `10.10.100.254`), and exported data (right-click on the Data row in the packet inspector) to my hex editor. I recommend the Hex Editor addon for VS Code.

The response looks like the following:
![Example response](../assets/exported_data.png)

Because we know that the integers are usually 2-byte and big-endian, we can go through the payload and check the data inspector (or convert the values manually if your hex editor doesn't support the feature) for our values in the screenshot. In the example above, I found out that the household load is contained in the response for the command `0x000d` at the address `0x0b`. Because appliances will never generate power (therefore there is no need for negative values), I can assume the value is unsigned - uint16_t data type (unsigned 2-byte integer).

## Conclusion
After finding out the command number and the data address in the response, it is required to find the appropriate request: just find the packet with the corresponding command number sent from the app to the inverter and copy the data.

After that, it is only a matter of adding a new function or extending the existing one.