"""
@File : docker_release_archive.py
@Date : 2024/9/19 上午10:28
@Author: 九层风（YePing Zhang）
@Contact : yeahcheung213@163.com
"""
import os
import subprocess

import requests
# 控制台样式库导入
from colorama import init, Fore, Back, Style

from parse_config import configuration

# 初始化颜色
init(autoreset=True)


# 执行cmd命令函数
def execute_cmd(cmd: str):
    try:
        result = subprocess.run(cmd, shell=True, check=True, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, encoding="utf-8", universal_newlines=True)
        return {"stdout": result.stdout, "stderr": result.stderr, "return_code": result.returncode}
    except subprocess.CalledProcessError as e:
        return {"stdout": e.stdout, "stderr": e.stderr, "return_code": e.returncode}
    except Exception as e:
        return {"stdout": None, "stderr": str(e), "return_code": 1}


# 控制台应用类
class ConsoleApp:
    """控制台应用"""

    # 构造菜单方法
    def __init__(self):
        self.menu_options = {
            '1': self.release_docker,
            '2': self.build_image_tar,
            '3': self.generate_deploy_script,
            '4': self.generate_upgrade_script,
            'q': self.exit_app
        }

    # 功能菜单显示方法
    @staticmethod
    def display_menu():
        welcome_text = "|--欢迎使用Docker镜像发布程序--|"
        print(Back.BLUE + Fore.BLACK + Style.BRIGHT + f"{welcome_text}")
        print(Fore.WHITE + Style.BRIGHT + "--------功能菜单----------")
        print(Fore.CYAN + Style.BRIGHT + "1. 发布镜像")
        print(Fore.GREEN + Style.BRIGHT + "2. 打包镜像(*.tar)")
        print(Fore.YELLOW + Style.BRIGHT + "3. 生成部署脚本")
        print(Fore.BLUE + Style.BRIGHT + "4. 生成升级脚本")
        print(Fore.MAGENTA + Style.BRIGHT + "q. 退出程序")
        print(Fore.WHITE + Style.BRIGHT + '-' * (len(welcome_text) + 6) + Style.RESET_ALL)

    # 主运行方法
    def run(self):
        while True:
            self.display_menu()
            choice = input(Fore.WHITE + Style.BRIGHT + "请输入您选择功能序号：").strip().lower()
            if choice in self.menu_options:
                self.menu_options[choice]()
            else:
                print(Fore.RED + "无效的选择，请重新输入！" + Style.RESET_ALL)

    # 选项方法
    @staticmethod
    def release_docker():
        print(Fore.LIGHTGREEN_EX + "功能【1.发布镜像】执行完毕！正在返回主菜单...\n")

    @staticmethod
    def build_image_tar():
        # 输入镜像地址，示例地址："192.168.1.33:8080/ewordarchive/ewordarchive-gen20241218:v1.0.13-x86-64"
        image_path = input(Fore.WHITE + Style.BRIGHT + "请输入镜像地址：").strip()
        # 输入tar包保存目录，输入D则表述输出到默认目录（当前目录的tmp文件夹）
        tar_path = input(
            Fore.WHITE + Style.BRIGHT + "请输入tar包保存目录，输入D则表述输出到默认目录（当前目录的tmp文件夹）：").strip().lower()
        if tar_path == "d":
            # 获取当前目录
            current_dir = os.getcwd()
            tar_path = os.path.join(current_dir, "tmp")
        # 取最后一个/之后的内容，将冒号替换成 -
        tar_file_name = image_path.split("/")[-1].replace(":", "-")
        # 拼接tar输出路径
        tar_file_path = f"{tar_path}/{tar_file_name}.tar"

        # 初始化 docker操作类
        doc = DockerOperationCli()
        # 先拉取镜像，本地存在不会重复拉取
        print(Fore.LIGHTYELLOW_EX + "[+] 1/2开始拉取镜像...")
        doc.pull_image_from_harbor(image_path)
        # 打包镜像
        print(Fore.LIGHTYELLOW_EX + f"[+] 2/2开始打包镜像，镜像地址：{image_path}，输出路径：{tar_file_path}...")
        doc.save_image_to_tar(image_path, tar_file_path)
        print(Fore.LIGHTGREEN_EX + "功能【打包镜像】执行完毕！正在返回主菜单...\n")

    @staticmethod
    def generate_deploy_script():
        pass
        print(Fore.LIGHTGREEN_EX + "功能【生成部署脚本】执行完毕！正在返回主菜单...\n")

    @staticmethod
    def generate_upgrade_script():
        pass
        print(Fore.LIGHTGREEN_EX + "功能【生成升级脚】执行完毕！正在返回主菜单...\n")

    @staticmethod
    def exit_app():
        print(Fore.LIGHTYELLOW_EX + "正在退出程序...")
        exit(0)


# docker操作类
class DockerOperationCli:
    """尝试docker的sdk不好用，所以直接使用命令方式调用"""

    def __init__(self):
        self.harbor_config = configuration.get("harbor")
        self.login_harbor_flag = self.login_harbor()

    # 检查docker服务是否启动
    @staticmethod
    def check_docker_service():
        check_cmd = "docker ps"
        print(f"校验docker服务是否启动...")
        check_result = execute_cmd(check_cmd)
        if check_result["return_code"] == 0:
            print(f"docker服务已启动！")
            print(f"{check_result['stdout']}")
            return True
        else:
            print(f"{check_result['stderr']}")
            return False

    # 登录harbor
    def login_harbor(self) -> bool:
        # 检查本地是否启动docker服务
        if not self.check_docker_service():
            print("docker服务未正常启动，请检查！")
            return False
        login_cmd = f"docker login {self.harbor_config['host']}"
        fill_user = f" --username={self.harbor_config['username']} --password={self.harbor_config['password']}"
        cmd_line = login_cmd + fill_user
        print(f"登录账号，执行命令：{cmd_line}")
        login_result = execute_cmd(cmd_line)
        if login_result["return_code"] == 0:
            print(f"{login_result['stdout']}")
            return True
        else:
            print(f"f{login_result['stderr']}")
            return False

    @staticmethod
    def pull_image_from_harbor(image_path):
        """
        :param image_path: 完整的镜像地址，eg：192.168.1.33:8080/ewordarchive/ewordarchive-gen20240903:v1.0.11-x86-64
        :return:
        """
        print(f"从harbor：{configuration.get('harbor').get('host')}拉取镜像...")
        pull_cmd = f"docker pull {image_path}"
        print(f"执行命令：{pull_cmd}")
        pull_result = execute_cmd(pull_cmd)
        if pull_result["return_code"] == 0:
            print(f"{pull_result['stdout']}")
            return True
        else:
            print(f"{pull_result['stderr']}")
            return False

    # 镜像打包
    @staticmethod
    def save_image_to_tar(image_name, tar_file_name):
        """
        :param image_name:为了保存的tar有tag，使用<镜像名>:<tag>的格式
        :param tar_file_name:
        :return:
        """
        print("保存镜像到本地...")
        save_cmd = f"docker save -o {tar_file_name} {image_name}"
        print(f"执行命令：{save_cmd}")
        save_result = execute_cmd(save_cmd)
        if save_result["return_code"] == 0:
            print(f"{save_result['stdout']}")
            return True
        else:
            print(f"f{save_result['stderr']}")
            return False


# 发布业务流程类
class ReleaseBusiness:
    def __init__(self):
        self.ci_host = configuration.get("ci").get("host")

    # 从CI接口获取版本发布信息
    def get_release_info(self, build_id: int):
        """
        根据禅道的版本id获取版本信息
        :param build_id:禅道版本id
        :return:
        """
        api_path = "/ewordci/build/get"
        result = requests.get(self.ci_host + api_path, params={"build_id": build_id})
        if result.status_code != 200:
            print(f"获取发布信息失败:{result.text}")
            return False
        if result.json()["code"] != 200:
            print(f"未获取到发布信息:{result.json()['message']}")
            return False
        print(f"获取到发布信息:{result.json()}")
        return result.json()

    # 解析发布信息
    @staticmethod
    def parse_release_info(image_url: str):
        """
        根据image在harbor的地址解析需要的信息，需要固定格式
        :param image_url: 如192.168.1.33:8080/ewordimcis/ewordimcis-nodeservice-gen20241126:v3.0.1-x86-64
        :return:需要的信息，dict
        """
        image_info = image_url.split("/")
        tar_name = image_info[-1].replace(":", "-")
        product_name = image_info[1]
        return {
            "product_name": product_name,
            "tar_name": tar_name
        }

    # 创建脚本

    # 版本打包

    # 程序归入悦库
    @staticmethod
    def program_into_ysh(program_directory):
        """
        1、遍历本地程序归档目录 程序包包含归档信息，如ewordimcis-2024-arm64-v1.2.4.7z
        2、给出程序目录列表
            1 -- ewordimcis-2024-arm64-v1.2.4.7z
            2 -- ewordris-2024-amd64-v1.2.4.7z
            3 -- ewordbds-2025-amd64-v1.2.3.7z
        3、输入序号
        4、选定对应的需要的程序包，上传至悦库
        :param program_directory:本地程序包目录
        :return:
        """
        program_files = [f for f in os.listdir(program_directory) if f.endswith('.7z')]

        # 按照文件名排序
        program_files.sort()

        # 打印列表及序号
        print(Fore.BLUE+"找到的程序包有：")
        for i, file in enumerate(program_files, start=1):
            print(f"{i}----{file}")

        # 获取用户输入
        while True:
            try:
                selected_file_index = input(Fore.LIGHTYELLOW_EX+"请输入要上传的程序包序号：")

                # 检查输入序号是否有效
                if 1 <= int(selected_file_index) <= len(program_files):
                    selected_file = program_files[int(selected_file_index) - 1]
                    print(f"已选择文件：{selected_file}")
                    return selected_file
                else:
                    print(Fore.RED+"无效的序号，请重新输入。")
            except ValueError:
                print(Fore.RED+"无效的输入，请重新输入。")



if __name__ == "__main__":
    # ConsoleApp().run()
    rb = ReleaseBusiness()
    rb.get_release_info(1414)
