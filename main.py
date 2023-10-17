import datetime
import json
import logging
import os
import re
from configparser import ConfigParser
from contextlib import suppress
from pathlib import Path

import requests

URL = os.environ.get("URL").strip()
PUSH_PLUS_TOKEN = os.environ.get("PUSH_PLUS_TOKEN", "").strip()
GITHUB_TRIGGERING_ACTOR = os.environ.get("GITHUB_TRIGGERING_ACTOR", "").strip()
config = ConfigParser()
config.read("config.ini", encoding="utf-8")
logging.basicConfig(level=logging.INFO)
logging.info(f"github.triggering_actor is {GITHUB_TRIGGERING_ACTOR}")


def pushplus():
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
    if config.getint("pushplus", "warning", fallback=10) > last:
        text = f"""# <text style="color:red;">警告：电量低于阈值({last_remain}kWh)</text>\n"""
    else:
        if config.getboolean("pushplus", "push_warning_only", fallback=False):
            return
        text = ""

    # TODO: buildid != real building ids
    text += f"## 当前剩余电量：{remain}kWh\n个人信息：{buildid[0]}号楼{roomid[0]}室\n\n统计时间：{stime}\n\n### 最近{days_to_show}天数据\n{tablestr}\n"

    tablestr = "| 序号 | 时间 | 剩余电量 |\n|---|---|---|\n"
    index = 1
    for item in reversed(last_few_items):
        tablestr += f'| {index} | {item["time"]} | {item["kWh"]}kWh |\n'
        index += 1

    if (
        config.getboolean("pushplus", "detail", fallback=True)
        and GITHUB_TRIGGERING_ACTOR
    ):
        website = (
            f"https://{GITHUB_TRIGGERING_ACTOR}.github.io/ecust-electricity-statistics"
        )
        text += f"[图表显示更多数据]({website})\n"
        logging.info("show more details")
    with suppress():
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

remain = float(re.findall((r"(\d+(\.\d+)?)度"), response.text)[0][0])
logging.info(f"剩余电量：{remain}")
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
originstring = json.dumps(data, indent=2, ensure_ascii=False)
Path("data.js").write_text("data=" + originstring, encoding="utf-8")
logging.info("write back to data.js")

if PUSH_PLUS_TOKEN:
    pushplus()
