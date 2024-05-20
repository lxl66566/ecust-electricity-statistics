import datetime
import json
import logging
import os
import re
from configparser import ConfigParser
from contextlib import suppress
from pathlib import Path

import requests

# DEBUG：开启调试模式，将 pushplus 消息输出至 stdout
DEBUG = os.environ.get("DEBUG", os.environ.get("debug", "")).strip()
URL = os.environ.get("URL").strip()
PUSH_PLUS_TOKEN = os.environ.get("PUSH_PLUS_TOKEN", "").strip()
GITHUB_TRIGGERING_ACTOR = os.environ.get("GITHUB_TRIGGERING_ACTOR", "").strip()

config = ConfigParser()
config.read("config.ini", encoding="utf-8")
logging.basicConfig(level=logging.INFO)
logging.info(f"{GITHUB_TRIGGERING_ACTOR=}")

# 你理的 buildid 真是太棒了
def building_number_map(id: int | str) -> int:
    match int(id):
        case x if x >= 27 and x <= 46:
            return x - 22
        case x if x >= 49 and x <= 52:
            return x - 24
        case other:
            return other

def pushplus():
    if not PUSH_PLUS_TOKEN and not DEBUG:
        logging.info("push plus token is empty, ignoring pushing...")
        return
    
    from urllib.parse import parse_qs, urlparse

    from utils import sendMsgToWechat

    parsed_url = urlparse(URL)
    params = parse_qs(parsed_url.query)
    roomid = params.get("roomid")
    buildid = params.get("buildid")
    stime = date  # TODO timezone
    days_to_show = config.getint("pushplus", "days_to_show", fallback=10)
    last_few_items = data[-days_to_show:]

    # insufficient electricity warning
    assert last_few_items, "last_few_items is empty"
    last_remain = last_few_items[-1]["kWh"]
    if config.getint("pushplus", "warning", fallback=10) > last_remain:
        text = f"""# <text style="color:red;">警告：电量低于阈值({last_remain}kWh)</text>\n"""
    else:
        if config.getboolean("pushplus", "push_warning_only", fallback=False) and not DEBUG:
            logging.info("sufficient electricity, ignoring pushing...")
            return
        text = ""

    tablestr = "| 序号 | 时间 | 剩余电量 |\n|---|---|---|\n"
    for index, item in enumerate(reversed(last_few_items), 1):
        tablestr += f'| {index} | {item["time"]} | {item["kWh"]}kWh |\n'

    text += f"## 当前剩余电量：{remain} kWh\n\n个人信息：{building_number_map(buildid[0])} 号楼 {roomid[0]} 室\n统计时间：{stime}\n\n### 最近 {days_to_show} 天数据\n\n{tablestr}\n"

    if (
        config.getboolean("pushplus", "detail", fallback=True)
        and GITHUB_TRIGGERING_ACTOR
    ):
        logging.info("show more details")
        text += f"[图表显示更多数据](https://{GITHUB_TRIGGERING_ACTOR}.github.io/ecust-electricity-statistics)\n"
    with suppress():
        if DEBUG:
            print(text)
        else:
            sendMsgToWechat(PUSH_PLUS_TOKEN, f"{stime}华理电费统计", text, "markdown")
        logging.info("push plus executed successfully")


# main
header = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Connection": "keep-alive",
    "Host": "yktyd.ecust.edu.cn",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Linux; U; Android 4.1.2; zh-cn; Chitanda/Akari) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30 MicroMessenger/6.0.0.58_r884092.501 NetType/WIFI",
}
response = requests.get(URL, headers=header)

try:
    remain = float(re.findall((r"(\d+(\.\d+)?)度"), response.text)[0][0])
    logging.info(f"剩余电量：{remain}")
except Exception as e:
    logging.exception(e)
    logging.error("剩余电量获取失败，response: " + response.text)

originstring = "[]"
date = datetime.datetime.now().strftime("%Y-%m-%d")

# read from data.js preprocessed as json
with suppress(FileNotFoundError):
    with open("data.js", "r", encoding="utf-8") as f:
        originstring = f.read().lstrip("data=")
try:
    data: list = json.loads(originstring)
except json.decoder.JSONDecodeError:
    logging.error("data.js 格式错误，请参考注意事项进行检查")
    exit(1)

# add new data
if data and (date in data[-1].values()):
    data[-1]["kWh"] = remain
else:
    data.append({"time": date, "kWh": remain})

# write back to data.js
if not DEBUG:
    originstring = json.dumps(data, indent=2, ensure_ascii=False)
    Path("data.js").write_text("data=" + originstring, encoding="utf-8")
    logging.info("write back to data.js")

pushplus()
