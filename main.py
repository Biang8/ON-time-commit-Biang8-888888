# main.py 主逻辑：包括字段拼接、模拟请求
import json
import time
import random
import logging
import hashlib
import requests
import urllib.parse
import os  # 读取环境变量
from config import get_book_info, REQUEST_DATA, HEADERS, COOKIES, PUSH_METHOD, READ_NUM
from push import push

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)-8s - %(message)s",
    handlers=[logging.FileHandler("wechat_read.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# API 地址
READ_URL = "https://weread.qq.com/web/book/read"
RENEW_URL = "https://weread.qq.com/web/login/renewal"
KEY = "your_secret_key_here"  # 请在此处配置你的密钥


def encode_data(params: dict) -> str:
    """对参数进行 URL 编码"""
    return "&".join([f"{k}={urllib.parse.quote(str(v), safe='')}" for k, v in sorted(params.items())])


def calculate_hash(data: str) -> str:
    """计算自定义哈希值"""
    _7032f5 = 0x15051505
    _cc1055 = _7032f5
    length = len(data)
    index = length - 1
    while index > 0:
        _7032f5 = (_7032f5 ^ (ord(data[index]) << ((length - index) % 30))) & 0x7FFFFFFF
        _cc1055 = (_cc1055 ^ (ord(data[index - 1]) << (index % 30))) & 0x7FFFFFFF
        index -= 2
    return hex(_7032f5 + _cc1055)[2:].lower()


def get_wr_skey():
    """刷新 cookie 密钥"""
    COOKIE_DATA = {"rq": "%2Fweb%2Fbook%2Fread"}
    response = requests.post(RENEW_URL, headers=HEADERS, cookies=COOKIES,
                             data=json.dumps(COOKIE_DATA, separators=(',', ':')))
    for cookie in response.headers.get('Set-Cookie', '').split(';'):
        if "wr_skey" in cookie:
            return cookie.split('=')[-1][:8]
    return None


def main():
    # 获取选定书籍，并更新请求数据中的 b 值
    selected_book, selected_b = get_book_info()
    REQUEST_DATA["b"] = selected_b

    logger.info(f"🎯 选定书籍: {selected_book} (b值: {selected_b})")
    total_read_time = 0.0
    index = 1
    while index <= READ_NUM:
        try:
            # 重新读取 READ_COMPLETE_HEADER（保证每次都使用最新的环境变量值）
            READ_COMPLETE_HEADER = os.getenv("READ_COMPLETE_HEADER", "🎉 微信读书自动阅读任务完成！")

            # 更新动态参数
            REQUEST_DATA["ct"] = int(time.time())
            REQUEST_DATA["ts"] = int(time.time() * 1000)
            REQUEST_DATA["rn"] = random.randint(0, 1000)
            REQUEST_DATA["sg"] = hashlib.sha256(f"{REQUEST_DATA['ts']}{REQUEST_DATA['rn']}{KEY}".encode()).hexdigest()
            REQUEST_DATA["s"] = calculate_hash(encode_data(REQUEST_DATA))

            logger.info(f"⏱️ 尝试第 {index} 次阅读...")
            response = requests.post(
                READ_URL,
                headers=HEADERS,
                cookies=COOKIES,
                data=json.dumps(REQUEST_DATA, separators=(",", ":")),
            )
            resData = response.json()

            if 'succ' in resData:
                total_read_time += 0.5
                index += 1
                time.sleep(30)  # 每次阅读间隔 30 秒
                logger.info(f"✅ 阅读成功，阅读进度：{total_read_time:.1f} 分钟")
            else:
                logger.warning("❌ cookie 已过期，尝试刷新...")
                new_skey = get_wr_skey()
                if new_skey:
                    COOKIES['wr_skey'] = new_skey
                    logger.info(f"✅ 密钥刷新成功，新密钥：{new_skey}")
                    logger.info(f"🔄 重新本次阅读。")
                else:
                    ERROR_CODE = "❌ 无法获取新密钥或者WXREAD_CURL_BASH配置有误，终止运行。"
                    logger.error(ERROR_CODE)
                    push(ERROR_CODE, PUSH_METHOD)
                    raise Exception(ERROR_CODE)
            REQUEST_DATA.pop('s')
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 网络请求失败: {str(e)}")
        except Exception as e:
            logger.error(f"❌ 发生未知错误: {str(e)}")
            break

    logger.info("🎉 阅读任务完成！")
    if PUSH_METHOD:
        try:
            message = (
                f"{READ_COMPLETE_HEADER}\n\n"
                f"📚 书籍：《{selected_book}》\n"
                f"⏱️ 阅读时长：{total_read_time:.1f}分钟\n"
                f"📅 完成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            push(message, PUSH_METHOD)
            logger.info("✅ 通知推送成功")
        except Exception as e:
            logger.error(f"❌ 通知推送失败: {str(e)}")


if __name__ == "__main__":
    main()