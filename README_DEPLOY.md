# Deployment Instructions

The bot is already deployed on the server. If you need to deploy it manually in the future, follow these steps:

1. SSH into the server (`51.20.117.210`) using the provided SSH key and `ec2-user`.
2. Navigate to `/home/ec2-user/bexruz_bot`.
3. If dependencies need to be installed, run `python3 -m pip install -r requirements.txt`.
4. Run the bot using `screen -dmS bexruz_bot bash /home/ec2-user/bexruz_bot/run.sh`.
