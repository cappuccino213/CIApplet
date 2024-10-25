"""
@File : release_archive.py
@Date : 2024/9/13 下午3:04
@Author: 九层风（YePing Zhang）
@Contact : yeahcheung213@163.com
"""
import os
import re
import subprocess

from parse_config import configuration

# 获取发布配置信息
config = configuration.get("release")


# 解析文件发布名称类
class AnalyzeReleaseName:
    def __init__(self, release_name: str):
        self.release_name = release_name
        self.release_info = self.analyze_release_info()

    # 解析出发布信息
    def analyze_release_info(self):
        # 先验证发布名称的格式
        pattern = r'^eWord[A-Za-z]+\s+[Vv](\d+([._]\d+)*)\.[a-zA-Z]+\.b\d{8}$'
        if not re.match(pattern, self.release_name):
            print("发布名称格式不正确,正确格式如：eWordRIS V1.2.4.5314.RTX.b20240531")
            return None, None, None
        try:
            # 获取产品名称
            product_name, version_info = self.release_name.split(" ")
            # 获取发布年份
            version_detail, release_year = version_info.split(".b")
            # 获取发布类型
            version_detail_list = version_detail.split(".")
            release_type = version_detail_list[-1]
            return product_name, release_type, release_year[:4]
        except Exception as e:
            print(f"解析发布名称失败:{e}")
            return None, None, None

    # 获取本地路径
    def get_local_path(self):
        local_root_path = config.get("release_local_path")
        # 获取遍历路径
        # release_info = self.analyze_release_info()
        release_info = self.release_info
        if release_info is None:
            return None
        local_dir = f"{local_root_path}\\{release_info[0]}\\{release_info[-1]}"
        print(f"遍历路径为：{local_dir}")
        # 遍历目录，找到包含发布名称的文件
        for root, dirs, files in os.walk(local_dir):
            for file in files:
                if self.release_name in file:
                    print(f"成功找到发布文件{file}")
                    return os.path.join(root, file)

    # 获取发布路径
    def get_release_path(self):
        release_root_path = config.get("release_root_path")
        # product_name, release_type, release_year = self.analyze_release_info()
        product_name, release_type, release_year = self.release_info
        if release_type in ("RTX", "RC", "M"):
            release_path = f"{release_root_path}/{product_name}/通用版本/{release_year}"
            print(f"发布路径为：{release_path}")
            return release_path
        if release_type in ("OEM", "Beta", "Alpha"):
            release_path = f"{release_root_path}/{product_name}/{release_type}版本/{release_year}"
            print(f"发布路径为：{release_path}")
            return release_path
        print("发布类型不正确，请检查发布名称")
        return None


# 命令交互类
class CommandConsole:
    def __init__(self):
        self.current_menu = self.main_menu
        self.run_flag = True

    # 运行
    def run(self):
        # while True:
        while self.run_flag:
            self.current_menu()

    # 执行cmd命令
    @staticmethod
    def execute_cmd(cmd: str):
        try:

            result = subprocess.run(cmd, shell=True, check=True, text=True, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, encoding="utf-8")
            return {"stdout": result.stdout, "stderr": result.stderr, "return_code": result.returncode}
        except subprocess.CalledProcessError as e:
            return {"stdout": e.stdout, "stderr": e.stderr, "return_code": e.returncode}
        except Exception as e:
            return {"stdout": None, "stderr": str(e), "return_code": 1}

    # 功能菜单
    def main_menu(self):
        print(f"{'*' * 10}欢迎使用 eWord发布归档系统{'*' * 10}")
        print("1正在检验ysh运行环境...")
        result = self.check_ysh()
        if result["return_code"] != 0:
            print("Error：ysh环境不正确，请检查ysh是否安装正确，且配置了环境变量")
            self.run_flag = False  # 环境不正确，退出程序
            input("按任意键退出程序...")
            return
        print(f"检验成功，ysh版本：{result['stdout']}")

        print("2正在完成用户信息配置...")
        login_result = self.ysh_login(config["ysk_url"], config["ysk_user"],
                                      config["ysk_password"])
        print(f"{login_result['stdout']}")

        if not self.check_ysh_login():
            print("Error：ysh登录失败，请检查配置文件中ysh账号是否正确")
            self.run_flag = False  # 账号错误，退出程序
            input("按任意键退出程序...")
            return

        release_name = input("3ysh登录成功，可以使用归档功能，请输入产品发布名称：")

        print(f"3正在解析发布名称...")
        release_info = AnalyzeReleaseName(release_name)
        if release_info.analyze_release_info() is None:
            print("发布名称不正确，请检查发布名称是否正确")
            return

        print(f"4正在进行文件归档...")
        result = self.ysh_put(release_info.get_local_path(), release_info.get_release_path())
        if result["return_code"] == 1:
            print(f"文件归档失败，ysh返回信息为：{result['stdout']}")
            return
        print(f"归档中：{result['stdout']}")

    """以下是ysh命令的调用方法"""

    # 查看ysh安装情况
    def check_ysh(self):
        cmd = "ysh --version"
        return self.execute_cmd(cmd)

    # 登录ysh账号
    def ysh_login(self, release_url: str, release_user: str, release_password: str):
        cmd = f"ysh user -u {release_url} -a {release_user} -p {release_password}"
        print(f"执行命令：{cmd}")
        return self.execute_cmd(cmd)

    # 清理当前登录用户的ysh登录信息
    def ysh_logout(self):
        cmd = "ysh user -c"
        return self.execute_cmd(cmd)

    # 上传文件
    def ysh_put(self, local_path: str, release_path: str):
        cmd = f'ysh put -f "{local_path}" {release_path}'
        return self.execute_cmd(cmd)

    # 检查登录账号
    def check_ysh_login(self):
        # cmd = "ysh get /公共空间/临时版本/测试上传/mysql相关.txt D:\\tmp "  # 本是获取文件方法，也可用来检测ysh是否登录
        cmd = "ysh get"  # 本是获取文件方法，也可用来检测ysh是否登录
        result = self.execute_cmd(cmd)
        # print(result["stdout"])
        if "账号或密码错误" in result["stdout"] or "请使用" in result["stdout"]:
            return False
        return True  # 表示登录成功


if __name__ == "__main__":
    # arn = AnalyzeReleaseName("eWordViewer v1.1.0.0_960.RTX.b20240510")
    # print(arn.analyze_release_info())
    # print(arn.get_local_path())
    # print(arn.get_release_path())
    # cc = CommandConsole().execute_cmd("ysh1 --version")
    # print(cc)
    command_console = CommandConsole()
    # command_console.check_ysh()
    # print(command_console.execute_cmd("ipconfig"))
    # print(command_console.ysh_login("http://192.168.1.19:2020", "robot", "Robot2024"))
    # print(command_console.ysh_logout())
    # print(command_console.check_ysh_login())

    command_console.run()
