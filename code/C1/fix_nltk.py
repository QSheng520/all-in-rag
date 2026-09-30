"""一键安装第一章示例所需的 NLTK 数据。

直接调用 nltk.download() 在国内网络下常常失败，原因有两个：
  1. 下载源 raw.githubusercontent.com 无法直连；
  2. NLTK 的 pathsec 会拒绝经由代理的下载请求，报 Security Violation（CWE-918）。
这里改为从镜像直接下载 zip 并解压到本地 nltk_data，绕开上述两个问题。

用法：python fix_nltk.py
"""
import os
import sys
import urllib.request
import zipfile

# 安装目录，可通过环境变量 NLTK_DATA 覆盖
NLTK_DATA_DIR = os.environ.get("NLTK_DATA") or os.path.join(
    os.path.expanduser("~"), "nltk_data"
)

# 需要的资源，key 是资源在 nltk_data 下的相对路径
# punkt_tab 与 averaged_perceptron_tagger_eng 供 unstructured（01）使用，stopwords 供 llama_index（02）使用
PACKAGES = (
    "tokenizers/punkt_tab",
    "taggers/averaged_perceptron_tagger_eng",
    "corpora/stopwords",
)

# 镜像地址，按顺序尝试
# cdn.jsdelivr.net 在国内时通时不通，所以放在后面当备用
MIRRORS = (
    "https://ghfast.top/https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages",
    "https://gh-proxy.com/https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages",
    "https://cdn.jsdelivr.net/gh/nltk/nltk_data@gh-pages/packages",
)

# 忽略系统代理：镜像本身可以直连，走不通的代理反而会失败
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def is_installed(relative_path):
    """必须已解压成普通目录才算装好。

    只放 zip 是不行的：unstructured 与 llama_index 都用精确目录匹配来检查资源是否存在，
    读不了 zip，会把已下载的资源判为缺失，每次启动都重新下载。
    """
    return os.path.isdir(os.path.join(NLTK_DATA_DIR, relative_path))


def download(relative_path):
    """从镜像下载并解压，成功返回 True。"""
    target_dir = os.path.dirname(os.path.join(NLTK_DATA_DIR, relative_path))
    os.makedirs(target_dir, exist_ok=True)

    for mirror in MIRRORS:
        url = "{}/{}.zip".format(mirror, relative_path)
        print("  下载 {}".format(url))
        try:
            # 部分镜像会拒绝默认的 Python-urllib User-Agent
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with OPENER.open(req, timeout=120) as resp:
                content = resp.read()
        except Exception as exc:
            print("  失败：{}: {}".format(type(exc).__name__, exc))
            continue

        # 先写临时文件再解压，避免半截文件被当成下载成功
        tmp_zip = os.path.join(target_dir, "__tmp__.zip")
        with open(tmp_zip, "wb") as f:
            f.write(content)
        with zipfile.ZipFile(tmp_zip) as zf:
            zf.extractall(target_dir)
        os.remove(tmp_zip)
        return True

    return False


def verify():
    """用 nltk 自己查一遍，确认资源真的能被找到。"""
    import nltk.data

    if NLTK_DATA_DIR not in nltk.data.path:
        nltk.data.path.insert(0, NLTK_DATA_DIR)

    ok = True
    for relative_path in PACKAGES:
        try:
            nltk.data.find(relative_path)
            print("[验证] {} 可用".format(relative_path))
        except LookupError:
            print("[验证] {} 找不到".format(relative_path))
            ok = False
    return ok


def main():
    print("NLTK 数据目录：{}".format(NLTK_DATA_DIR))

    failed = []
    for relative_path in PACKAGES:
        if is_installed(relative_path):
            print("[跳过] {} 已存在".format(relative_path))
            continue

        print("[安装] {}".format(relative_path))
        if download(relative_path):
            print("[完成] {}".format(relative_path))
        else:
            failed.append(relative_path)

    print()
    if failed:
        print("以下资源安装失败，请检查网络，或手动下载后解压到对应目录：")
        for relative_path in failed:
            print("  - {}.zip  ->  {}/".format(relative_path, relative_path))
        return 1

    if not verify():
        return 1

    print("\n全部就绪，现在可以运行 01_langchain_example.py 与 02_llamaIndex_example.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
