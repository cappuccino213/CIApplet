"""
@File : docker_release_archive.py
@Date : 2024/9/19 上午10:28
@Author: 九层风（YePing Zhang）
@Contact : yeahcheung213@163.com
"""
import os
import subprocess
import time
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


# 控制台列表函数
def show_list(data: list):
    """
    将list数据在控制台以列表的形式显示
    并在前序号，提供选择功能
    :param data: 选项的名称列表
    :return: 选中的行组成的新列表
    """
    for index, item in enumerate(data, start=1):
        print(Fore.CYAN + f"{index}. {item}")
    while True:
        try:
            input_index = input(
                Fore.LIGHTYELLOW_EX + "请输入选项的序号：单选直接输入序号，多选以英文逗号隔开（如1,2,3,4），全选输入a！")
            # 获取输入的选项序号
            if input_index.lower() == "a":
                selected_index = range(1, len(data) + 1)
            else:
                selected_index = input_index.split(',')
            # 获取对应的元素名
            selected_real_options = []
            for index in selected_index:
                # 检查输入序号是否有效
                if 1 <= int(index) <= len(data):
                    selected_file = data[int(index) - 1]
                    selected_real_options.append(selected_file)
            print(Fore.LIGHTGREEN_EX + f"选择的有效选项：{selected_real_options}")
            if len(selected_real_options) == 0:
                print(Fore.RED + "无有效的序号，请重新输入!!!")
                continue
            return selected_real_options
        except ValueError:
            print(Fore.RED + "无效的输入，请重新输入!!!")


# 文件处理类
class FileHandle:
    """文件处理类"""

    @staticmethod
    # 获取文件最后更新时间函数
    def get_file_last_modified_time(file_path):
        """
        获取文件最后更新时间
        :param file_path: 文件路径
        :return: 文件最后更新时间
        """
        # 获取文件最后修改时间
        last_modified_time = os.path.getmtime(file_path)
        readable_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last_modified_time))
        # print(readable_time)
        return readable_time

    # 找到程序包函数
    @staticmethod
    def find_the_specified_suffix_file(zip_directory: str, suffix: str):
        """
        找出指定文件后缀的文件，并列出标号，以7z为例
        1、遍历本地7z文件，如ewordimcis-2024-arm64-v1.2.4.7z
        2、给出程序目录列表
            1 ewordimcis-2024-arm64-v1.2.4.7z
            2 ewordris-2024-amd64-v1.2.4.7z
            3 ewordbds-2025-amd64-v1.2.3.7z
        3、输入序号，支持多选，以空格分隔，全选输入a回车
        4、输出对应文件名列表
        :param zip_directory:本地程序包目录
        :return:7z包文件名列表
        """
        program_files = [f for f in os.listdir(zip_directory) if f.endswith(suffix)]
        # 按照文件名排序
        program_files.sort()
        if len(program_files) == 0:
            print(Fore.BLUE + "未找到7z包")
            return []
        # 打印列表及序号
        print(Fore.BLUE + f"发现{suffix}包如下列表：")
        return show_list(program_files)

    @staticmethod
    # 清除文件函数
    def remove_file(file_path_list):
        """
        :param file_path_list: 文件路径列表
        :return:
        """
        for file_path in file_path_list:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(Fore.LIGHTGREEN_EX + f"已删除文件：{file_path}")
            else:
                print(Fore.RED + f"文件不存在：{file_path}")


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

    # 镜像重命名+tag
    @staticmethod
    def tag_image(image_tar_name, new_image_tar_name):
        """
        :param image_tar_name:旧的镜像名
        :param new_image_tar_name:tag名
        :return:
        """
        tag_cmd = f"docker tag {image_tar_name} {new_image_tar_name}"
        print(f"执行命令：{tag_cmd}")
        tag_result = execute_cmd(tag_cmd)
        if tag_result["return_code"] == 0:
            print(f"{tag_result['stdout']}")
            return True
        else:
            print(f"{tag_result['stderr']}")
            return False

    # 镜像打包
    @staticmethod
    def save_image_to_tar(image_name, tar_file_name):
        """
        :param image_name:为了保存的tar有tag，使用<镜像名>:<tag>的格式
        :param tar_file_name:tar文件路径
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


# ydisk操作类
class YDiskOperationCli:
    def __int__(self):
        self.ydisk_config = configuration.get("ydisk")
        self.login_ydisk_flag = self.login_ydisk()

    # 登录ydisk
    def login_ydisk(self):
        cmd = f"ysh user -u {self.ydisk_config.get('ysk_url')} -a {self.ydisk_config.get('ysk_user')} -p {self.ydisk_config.get('ysk_password')}"
        print(Fore.LIGHTBLUE_EX + f"执行命令：{cmd}")
        return execute_cmd(cmd)

    # 检查文件夹是否存在
    def check_folder_exist(self, folder_path: str):
        """
        :param folder_path:文件夹路径
        :return:
        """
        cmd = f"ysh ls {folder_path}"
        print(Fore.BLUE + f"执行命令：{cmd}")
        if execute_cmd(cmd)["return_code"] == 0:
            print(Fore.LIGHTRED_EX + f"{folder_path}已存在")
            return True
        else:
            print(Fore.LIGHTGREEN_EX + f"{folder_path}不存在")
            return False

    # 新建文件夹
    def create_folder(self, folder_path: str):
        """
        :param folder_path:文件夹路径
        :return:
        """
        # 先判断文件夹是否存在
        if self.check_folder_exist(folder_path):
            return True
        cmd = f"ysh mkdir {folder_path}"
        print(Fore.BLUE + f"执行命令：{cmd}")
        if execute_cmd(cmd)["return_code"] == 0:
            print(f"{folder_path}创建成功")
            return True
        else:
            print(f"{folder_path}创建失败")
            return False

    # 上传文件
    def upload_file(self, local_path: str, release_path: str):
        """
        :param local_path:本地文件路径
        :param release_path:发布路径（文件夹）
        :return:
        """
        cmd = f"ysh put -f {local_path} {release_path}"
        print(Fore.BLUE + f"执行命令：{cmd}")
        if execute_cmd(cmd)["return_code"] == 0:
            print(f"{local_path}上传成功")
            return True
        else:
            print(f"{local_path}上传失败")


# 发布业务流程类
class ReleaseBusiness:
    def __init__(self):
        self.ci_host = configuration.get("ci").get("host")
        self.release_config = configuration.get("release")

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
        return result.json()['data'][0]

    # 提取发布信息
    @staticmethod
    def extract_release_info(image_url: str):
        """
        根据image在harbor的地址解析需要的信息，需要固定格式
        :param image_url: 如192.168.1.33:8080/ewordimcis/ewordimcis-nodeservice-gen20241126:v3.0.1-x86-64
        :return:需要的信息，dict
        """
        image_info = image_url.split("/")
        product_name = image_info[1]
        tag = image_url.split(":")[-1]
        # ori_image_name = "".join(image_url.split(":")[:-1])
        new_image_name = image_info[-1].split(":")[0]
        ori_image_name = f"{image_info[0]}/{image_info[1]}/{new_image_name}"

        return {
            "product_name": product_name,
            "ori_image_name": ori_image_name,
            "new_image_name": new_image_name,
            "tag": tag,
            "tar_name": f"{new_image_name}-{tag}.tar"
        }

    # --打包tar
    def package_image_tar(self):
        """
        根据输入的镜像信息打包成tar文件
        可以为禅道的版本id或者harbor镜像地址，用不同的标记区分
        id 1414  # 表示从id获取信息间接获取
        url 192.168.1.33:8080/ewordimcis/nodeservice-gen20241126:v3.0.1-x86-64  # 表示直接拉取
        :return:
        """
        print(Fore.LIGHTBLUE_EX + Style.BRIGHT + """按如下格式输入
        id 1414    id<空格><禅道版本id>（从禅道的id获取信息间接获取）
        url 192.168.1.33:8080/ewordimcis/nodeservice-gen20241126:v3.0.1-x86-64   url<空格><镜像地址>（表示直接从harbor拉取）
        """)
        while True:
            image_info = input(Fore.WHITE + Style.BRIGHT + "请输入:").strip().lower()
            # 判断输入的格式
            if "id " not in image_info and "url " not in image_info:
                print(Fore.RED + "输入格式错误，请重新输入")
                continue
            image_url = ""
            if image_info.startswith("id"):
                build_id = int(image_info.split(" ")[1])
                image_url = self.get_release_info(build_id)["filePath"]
            if image_info.startswith("url"):
                image_url = image_info.split(" ")[1]
            if image_url:
                doc = DockerOperationCli()
                if not doc.login_harbor_flag:
                    # print(Fore.RED + "请先登录harbor")
                    return False
                # 拉取镜像
                print(Fore.LIGHTYELLOW_EX + "[+] 1/3开始拉取镜像...")
                if doc.pull_image_from_harbor(image_url):
                    # 解析镜像信息
                    release_info = self.extract_release_info(image_url)
                    # 提取镜像tar构建信息
                    ori_image_name = release_info["ori_image_name"]
                    new_image_name = release_info["new_image_name"]
                    tag = release_info["tag"]

                    # 为了避免暴露镜像地址，镜像名称剔除harbor地址，所以重新打TAG
                    print(Fore.LIGHTYELLOW_EX + f"[+] 2/3 开始重新打TAG...")
                    tag_result = doc.tag_image(f"{ori_image_name}:{tag}", f"{new_image_name}:{tag}")
                    if not tag_result:
                        return False
                    tar_path = os.path.join(os.getcwd(), "image_tar", release_info["tar_name"])
                    # 打包镜像
                    # print(Fore.LIGHTYELLOW_EX + f"[+] 3/3开始打包镜像，镜像地址：{image_url}，输出路径：{tar_path}...")
                    print(
                        Fore.LIGHTYELLOW_EX + f"[+] 3/3开始打包镜像，镜像地址：{new_image_name}:{tag}，输出路径：{tar_path}...")
                    return doc.save_image_to_tar(f"{new_image_name}:{tag}", tar_path)
            else:
                print(Fore.RED + "镜像拉取失败，请检查镜像地址或版本id是否关联镜像")
                continue

    # --创建脚本
    def create_deploy_script(self):
        pass

    # 版本打包(tar+脚本)

    # 程序归入悦库、共享库
    def upload_release_to_ydisk(self):
        # 获取预发布文件夹路径
        rc_real_path = os.path.join(os.getcwd(), self.release_config.get("rc_src_path"))
        # 获取预发布文件列表
        print(Fore.LIGHTBLUE_EX + "待发布7z文件列出,请选择...")
        rc_file_list = FileHandle.find_the_specified_suffix_file(rc_real_path, ".7z")

        # 解析出对应的悦库上传路径
        print(Fore.LIGHTYELLOW_EX + "[+] 1/2开始解析上传文件路径...")
        release_ydisk_path = self.release_config.get("release_ydisk_path")
        release_detail_paths = []
        ydoc = YDiskOperationCli()
        for rc_file in rc_file_list:
            rc_file_names = rc_file.split("-")
            first_path, second_path, third_path = rc_file_names[0], rc_file_names[1], rc_file_names[2][:4]
            # 因为ydisk不支持全路径创建，所以需要逐级创建
            ydoc.create_folder(release_ydisk_path + "/" + first_path)
            ydoc.create_folder(release_ydisk_path + "/" + first_path + "/" + second_path)
            ydoc.create_folder(release_ydisk_path + "/" + first_path + "/" + second_path + "/" + third_path)
            release_detail_paths.append(release_ydisk_path + "/" + first_path + "/" + second_path + "/" + third_path)
        print(release_detail_paths)

        # 上传文件
        print(Fore.LIGHTYELLOW_EX + "[+] 2/2开始上传文件...")
        for rc_file, release_path in zip(rc_file_list, release_detail_paths):
            rc_file_path = os.path.join(rc_real_path, rc_file)
            print(Fore.LIGHTYELLOW_EX + f"开始上传文件：{rc_file_path}，上传路径：{release_path}")
            ydoc.upload_file(rc_file_path, release_path)

    # --清理指定后缀文件
    @staticmethod
    def clean_local_file(directory: str, suffix: str):
        """
        :param directory: 程序根目录下的文件夹路径，如release_base  image_tar
        :param suffix: 文件后缀名
        :return:
        """
        # 获取指定文件夹路径
        rc_real_path = os.path.join(os.getcwd(), directory)
        # 获取指定文件列表
        rc_file_list = FileHandle.find_the_specified_suffix_file(rc_real_path, suffix)
        # 获取指定文件路径
        rc_file_path = [os.path.join(rc_real_path, rc_file_name) for rc_file_name in rc_file_list]
        # 清除文件
        FileHandle.remove_file(rc_file_path)

    # 清除tar文件
    def clean_tar_file(self):
        self.clean_local_file("image_tar", ".tar")

    # 清除预发布文件
    def clean_rc_srcs(self):
        self.clean_local_file(self.release_config.get("rc_src_path"), ".7z")


# 控制台应用类
class ConsoleApp:
    """控制台应用"""

    # 构造菜单方法
    def __init__(self):
        self.menu_options = {
            '1': self.build_image_tar,
            '2': self.generate_deploy_script,
            '3': self.generate_upgrade_script,
            '4': self.release_docker,
            '5': self.clean_rc_srcs,
            '6': self.clean_tar_file,
            'q': self.exit_app
        }

    # 功能菜单显示方法
    @staticmethod
    def display_menu():
        welcome_text = "|--欢迎使用Docker镜像发布程序--|"
        print(Back.BLUE + Fore.BLACK + Style.BRIGHT + f"{welcome_text}")
        print(Fore.WHITE + Style.BRIGHT + "--------功能菜单----------")
        print(Fore.GREEN + Style.BRIGHT + "1. 打包镜像(*.tar)")
        print(Fore.YELLOW + Style.BRIGHT + "2. 生成部署脚本")
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "3. 生成升级脚本")
        print(Fore.CYAN + Style.BRIGHT + "4. 发布镜像")
        print(Fore.RED + Style.BRIGHT + "5. 清除发布源文件")
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "6. 清除打包文件")
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
    # def build_image_tar():
    #     # 输入镜像地址，示例地址："192.168.1.33:8080/ewordarchive/ewordarchive-gen20241218:v1.0.13-x86-64"
    #     image_path = input(Fore.WHITE + Style.BRIGHT + "请输入镜像地址：").strip()
    #     # 输入tar包保存目录，输入D则表述输出到默认目录（当前目录的tmp文件夹）
    #     tar_path = input(
    #         Fore.WHITE + Style.BRIGHT + "请输入tar包保存目录，输入D则表述输出到默认目录（当前目录的tmp文件夹）：").strip().lower()
    #     if tar_path == "d":
    #         # 获取当前目录
    #         current_dir = os.getcwd()
    #         tar_path = os.path.join(current_dir, "tmp")
    #     # 取最后一个/之后的内容，将冒号替换成 -
    #     tar_file_name = image_path.split("/")[-1].replace(":", "-")
    #     # 拼接tar输出路径
    #     tar_file_path = f"{tar_path}/{tar_file_name}.tar"
    #
    #     # 初始化 docker操作类
    #     doc = DockerOperationCli()
    #     # 先拉取镜像，本地存在不会重复拉取
    #     print(Fore.LIGHTYELLOW_EX + "[+] 1/2开始拉取镜像...")
    #     doc.pull_image_from_harbor(image_path)
    #     # 打包镜像
    #     print(Fore.LIGHTYELLOW_EX + f"[+] 2/2开始打包镜像，镜像地址：{image_path}，输出路径：{tar_file_path}...")
    #     doc.save_image_to_tar(image_path, tar_file_path)
    #     print(Fore.LIGHTGREEN_EX + "功能【打包镜像】执行完毕！正在返回主菜单...\n")
    def build_image_tar():
        ReleaseBusiness().package_image_tar()
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
    def release_docker():
        print(Fore.LIGHTGREEN_EX + "已进入【发布镜像】功能...")
        ReleaseBusiness().upload_release_to_ydisk()
        print(Fore.LIGHTGREEN_EX + "功能【发布镜像】执行完毕！正在返回主菜单...\n")

    # 清除预发布程序源
    @staticmethod
    def clean_rc_srcs():
        print(Fore.LIGHTGREEN_EX + "已进入【清除预发布源】功能...")
        ReleaseBusiness().clean_rc_srcs()
        print(Fore.LIGHTGREEN_EX + "功能【清除预发布源】执行完毕！正在返回主菜单...\n")

    @staticmethod
    def clean_tar_file():
        print(Fore.LIGHTGREEN_EX + "已进入【清除打包文件】功能...")
        ReleaseBusiness().clean_tar_file()
        print(Fore.LIGHTGREEN_EX + "功能【清除预发布源】执行完毕！正在返回主菜单...\n")

    @staticmethod
    def exit_app():
        print(Fore.LIGHTYELLOW_EX + "正在退出程序...")
        exit(0)


if __name__ == "__main__":
    ConsoleApp().run()
    # rb = ReleaseBusiness()
    # rb.upload_release_to_ydisk()
    # rb.get_release_info(1414)
    # rb.clean_local_file()
