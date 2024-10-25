"""
@File : docker_release_archive.py
@Date : 2024/9/19 上午10:28
@Author: 九层风（YePing Zhang）
@Contact : yeahcheung213@163.com
"""

# 控制台样式库导入
from colorama import init, Fore, Back, Style

from release_config import *

import docker

# 初始化颜色
init(autoreset=True)


# 控制台应用类
class ConsoleApp:
    # 构造菜单方法
    def __init__(self):
        self.menu_options = {
            '1': self.function_1,
            '2': self.build_image_tar,
            '3': self.function_3,
            '4': self.function_4,
            'q': self.exit_app
        }

    # 功能菜单显示方法
    def display_menu(self):
        welcome_text = "|--欢迎使用Docker镜像发布程序--|"
        print(Back.BLUE + Fore.BLACK + Style.BRIGHT + f"{welcome_text}")
        print(Fore.WHITE + Style.BRIGHT + "--------功能菜单----------")
        print(Fore.CYAN + Style.BRIGHT + "1. 发布镜像")
        print(Fore.GREEN + Style.BRIGHT + "2. 构建镜像(*.tar)")
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

    # 功能运行提示方法
    def menu_tips(self, function):
        pass

    # 选项方法
    def function_1(self):
        pass
        print(Fore.LIGHTGREEN_EX + "功能【1.发布镜像】执行完毕！正在返回主菜单...\n")

    def build_image_tar(self):
        pass
        print("功能2执行完毕！")

    def function_3(self):
        pass
        print("功能3执行完毕！")

    def function_4(self):
        pass
        print("功能4执行完毕！")

    @staticmethod
    def exit_app():
        print(Fore.LIGHTYELLOW_EX + "正在退出程序...")
        exit(0)


# Docker操作类
class DockerOperation:
    def __init__(self, auth_config):
        # 从环境变量读取客户端配置，与Docker命令行客户端使用的环境变量相同
        client = docker.from_env()

        self.images = client.images()
        self.auth_config = auth_config

    # 从Harbor仓库拉取镜像
    def pull_image_from_harbor(self, image_path):
        """
        :param image_path: 完整的镜像地址，eg：192.168.1.33:8080/ewordarchive/ewordarchive-gen20240903:v1.0.11-x86-64
        :return:
        """
        print("从harbor拉取镜像...")
        self.images.pull(repository=image_path, auth_config=self.auth_config)


    def save_image_to_tar(self, image_name, tar_file_name):
        print("保存镜像到本地...")
        with open(tar_file_name, 'wb') as f:
            image_data = self.images.get(image_name).save(named=True)
            for chunk in image_data:
                f.write(chunk)


# 脚本生成类

# 获取产品名称和TAG

if __name__ == "__main__":
    # ConsoleApp().run()
    img_name = "192.168.1.33:8080/ewordarchive/ewordarchive-gen20240903:v1.0.11-x86-64"

    tar_file = r"./tmp/ewordarchive-gen20240903:v1.0.11-x86-64.tar"
    docker_manager = DockerOperation(auth_config=harbor_config)
    docker_manager.pull_image_from_harbor(image_path=img_name)
    docker_manager.save_image_to_tar(image_name=img_name, tar_file_name=tar_file)
