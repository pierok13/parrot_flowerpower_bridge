# parrot_flowerpower_bridge
Python Bridge for Parrot FlowerPower with Bluetooth and Cloud API

# Usage
crontab -e
*/15 * * * * python /home/pi/flowerPowerCloudMqtt.py

sudo crontab -e
/15 * * * * cd /home/pi && python /home/pi/flowerPowerBridge.py
