# lerobot-Follower_sees_follower_does

This a setup for mimicking movement of S0-101 Leader arm (moved by hand) by the corresponding Follower arm.
Equipment:
 - SO-101 follower arm with a control board
 - SO-101 leader arm with a control board
 - 2 * power suppliers (5V)
 - 2 * USB-C cables

The main script is follower_sees_follower_does.py. It should run as expected without special adjustments, but a few things must be set up in the code, while the two arms are connected to power and to computer:
- Ports - check the port names of the two arms, and update them in the script
- Motor IDs - in the script, the servo motors IDs are oredered the way we set them up in the lab. For any other order, they should be ordered in the Python list by the order of joints in the [official assembly guide]([url](https://huggingface.co/docs/lerobot/so101)). Note that in our setup the motors were ordered from 1 to 12 (follower first), apart from motors 5 and 6, which are swapped.

### What it does
After running follower_sees_follower_does.py while the two arms are connected, you will be asked to move the two to the exact same position. It is required as the follower's moves will be in relation to the leader's, regardless of the starting point. After positioning, hit enter and the two arms will be in sync.

### Modifications & Troubleshooting
###### Motor ID
If you wish to change a motor ID, there is a provided script for that. To run the script, set the old ID constant in the code (the default is 1, if you don't know there a script provided), and to run from the terminal, type python set_motor_id.py new_id. Note that only a single motor can be connected at a time, and remember to change the port name.

###### Scan motors
To check which motors are connected, run the script scan_motors.py. It will print all IDs of discovered motors. If two motors share the same ID, the script won't differentiate between them.
