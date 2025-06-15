# -ip-
本程序为开源程序，使用python编译
使用telegram bot来实现vps nat的共享ipv4/vps动态ip类型的更换通知
PS：一个小玩意，适合懒人，只需要打开dns解析网站手动更换就行。没做全自动的ddns设置，有需要的可以在此基础上增加来实现全自动ddns+tgbot通知。
推荐大家使用debian12系统（内置自带python）

安装pip3

apt update && apt install -y python3-pip

强制安装python-telegram-bot库（系统全局状态。适合懒人，绕过系统限制来安装。我更推荐懂的人使用独立虚拟环境）

pip3 install python-telegram-bot requests --break-system-packages

后台运行文件（防止关闭vps导致不运行）

nohup python3 vpsdtipzdtzbot.py > bot.log 2>&1 &

查看该程序状态

ps aux | grep vpsdtipzdtzbot.py

停止运行

pkill -f vpsdtipzdtzbot.py
