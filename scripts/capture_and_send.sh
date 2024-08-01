#!/bin/bash

LOGFILE="/home/marginx/workspace/amd/capture_and_send_text.log"
echo "Running capture_and_send_text.sh" > $LOGFILE

# 使用xdotool捕获选中文本
xdotool sleep 0.100 getactivewindow key ctrl+c
echo "Pressed Ctrl+C" >> $LOGFILE

sleep 0.5  # 等待剪贴板更新
echo "Clipboard updated" >> $LOGFILE

# 从剪贴板读取文本
text=$(xclip -o -selection clipboard)
echo "Clipboard text: $text" >> $LOGFILE

# 调用Flask后端的接口将文本发送过去
curl -X POST -d "text=$text" http://127.0.0.1:8000/add_text >> $LOGFILE 2>&1

