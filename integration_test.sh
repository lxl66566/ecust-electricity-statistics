#!/bin/bash
export DEBUG=1
export URL='https://yktyd.ecust.edu.cn/epay/wxpage/wanxiao/eleresult?sysid=1&roomid=607&areaid=2&buildid=30'  # random choice
export PUSH_PLUS_TOKEN=''   # add your token
export GITHUB_TRIGGERING_ACTOR='test'
export TELEGRAM_BOT_TOKEN=''  # add your token
export TELEGRAM_USER_IDS=''  # add your id
uv run python main.py