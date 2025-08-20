import requests
import os
import re
import json
import datetime


def trigger_github_action(update_info: dict):
    """
    触发一个 GitHub Action 工作流的 dispatch 事件。
    """
    try:
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            print("GITHUB_TOKEN 未设置，无法触发 GitHub Action。")
            return

        headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        }
        body = {"event_type": "update_available", "client_payload": update_info}

        # 使用 requests.post 来发送请求，并设置超时
        webhook_response = requests.post(
            "https://api.github.com/repos/Xerxes-2/AutoLiqi/dispatches",
            headers=headers,
            json=body,
            timeout=10,  # 设置超时时间为 10 秒
        )
        webhook_response.raise_for_status()  # 如果响应状态码是 4xx/5xx，则抛出 HTTPError

        print("成功触发 GitHub Action")

    except requests.exceptions.HTTPError as e:
        print(
            f"触发 GitHub Action 失败：发生 HTTP 错误：{e.response.status_code} - {e.response.text}"
        )
        raise
    except requests.exceptions.RequestException as e:
        print(f"触发 GitHub Action 失败：发生网络错误：{e}")
        raise
    except Exception as e:
        print(f"触发 GitHub Action 时发生意外错误：{e}")
        raise


def check_updates():
    """
    通过比较雀魂游戏版本和 GitHub 发布版本来检查更新。
    """
    try:
        # 从 maj-soul 获取当前版本
        version_response = requests.get(
            "https://game.maj-soul.com/1/version.json", timeout=10
        )
        version_response.raise_for_status()
        version_data = version_response.json()
        version = version_data["version"]

        # 获取 protobuf 前缀
        res_version_response = requests.get(
            f"https://game.maj-soul.com/1/resversion{version}.json", timeout=10
        )
        res_version_response.raise_for_status()
        res_version_data = res_version_response.json()
        liqi_prefix = (
            res_version_data.get("res", {})
            .get("res/proto/liqi.json", {})
            .get("prefix", "")
        )
        lqbin_prefix = (
            res_version_data.get("res", {})
            .get("res/config/lqc.lqbin", {})
            .get("prefix", "")
        )

        # 获取最新的 GitHub Release
        github_token = os.getenv("GITHUB_TOKEN")
        github_headers = {"X-GitHub-Api-Version": "2022-11-28"}
        if github_token:
            github_headers["Authorization"] = f"Bearer {github_token}"

        github_response = requests.get(
            "https://api.github.com/repos/Xerxes-2/AutoLiqi/releases/latest",
            headers=github_headers,
            timeout=10,
        )

        if github_response.headers.get("X-RateLimit-Remaining") == "0":
            raise Exception("GitHub API 速率限制已超出")

        github_response.raise_for_status()
        github_data = github_response.json()
        current_tag = github_data.get("tag_name", "")

        # 解析 Release 描述以获取当前的 lqbin 版本
        description = github_data.get("body", "")
        lqbin_match = re.search(r"lqc\.lqbin\s+(\S+)", description)
        current_lqbin_version = lqbin_match.group(1) if lqbin_match else ""

        # 检查是否需要更新
        liqi_update_needed = current_tag != liqi_prefix
        lqbin_update_needed = current_lqbin_version != lqbin_prefix
        update_needed = liqi_update_needed or lqbin_update_needed

        # 构建结果字典
        result = {
            "updateNeeded": update_needed,
            "liqiUpdateNeeded": liqi_update_needed,
            "lqbinUpdateNeeded": lqbin_update_needed,
            "currentVersions": {
                "version": version,
                "liqiPrefix": liqi_prefix,
                "lqbinPrefix": lqbin_prefix,
                "currentTag": current_tag,
                "currentLqbinVersion": current_lqbin_version,
            },
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

        print("更新检查结果:", json.dumps(result, indent=2))

        # 如果需要更新，则模拟触发 webhook
        if update_needed:
            print("需要更新！将触发 GitHub Action...")
            if github_token:
                trigger_github_action(result)
            else:
                print("GITHUB_TOKEN 未设置，跳过 webhook 触发")
        else:
            print("无需更新")

        return result

    except requests.exceptions.HTTPError as e:
        print(
            f"检查更新时发生错误：HTTP 错误：{e.response.status_code} - {e.response.text}"
        )
        raise
    except requests.exceptions.RequestException as e:
        print(f"检查更新时发生错误：网络错误：{e}")
        raise
    except Exception as e:
        print(f"检查更新时发生意外错误：{e}")
        raise


# 运行检查函数
if __name__ == "__main__":
    try:
        check_updates()
    except Exception as e:
        print(f"脚本执行失败：{e}")
