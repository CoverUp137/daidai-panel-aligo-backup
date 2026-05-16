#!/usr/bin/env python3
# coding: utf-8
'''
cron: 0 2 * * *
new Env('daidai-panel备份');
'''
import logging
import os
import sys
import tarfile
import time

from aligo import Aligo

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

try:
    from notify import send
except:
    logger.info("无推送文件")


def env(key):
    return os.environ.get(key)


# ==================== 呆呆面板适配配置 ====================
# 呆呆面板数据目录（Docker 内默认 /app/Dumb-Panel）
DD_DATA_DIR = '/app/Dumb-Panel'

# 排除目录名（logs 任务执行日志通常很大，backups 避免循环备份）
DD_EXCLUDE_NAMES = ['logs', 'backups']
if env("DD_EXCLUDE_NAMES"):
    DD_EXCLUDE_NAMES = env("DD_EXCLUDE_NAMES").split(",")
    logger.info(f'检测到设置变量 DD_EXCLUDE_NAMES={DD_EXCLUDE_NAMES}')

# 备份目标目录（本地存放 tar.gz 的目录）
DD_BACKUPS_PATH = 'backups'  # 默认在 /app/Dumb-Panel/backups/
if env("DD_BACKUPS_PATH"):
    DD_BACKUPS_PATH = str(env("DD_BACKUPS_PATH"))
    logger.info(f'检测到设置变量 DD_BACKUPS_PATH={DD_BACKUPS_PATH}')

# 最大备份保留数量（本地 + 云端统一控制）
DD_MAX_FILES = 5
if env("DD_MAX_FILES"):
    DD_MAX_FILES = int(env("DD_MAX_FILES"))
    logger.info(f'检测到设置变量 DD_MAX_FILES={DD_MAX_FILES}')

# 阿里云盘备份目录名
DD_ALI_FOLDER = 'daidai-panel-backups'
if env("DD_ALI_FOLDER"):
    DD_ALI_FOLDER = str(env("DD_ALI_FOLDER"))
    logger.info(f'检测到设置变量 DD_ALI_FOLDER={DD_ALI_FOLDER}')
# ======================================================


def start():
    """开始备份"""
    logger.info('将呆呆面板所需数据目录进行压缩...')

    # 切换到数据目录上级，以便 tar 内保留 Dumb-Panel/ 目录结构
    os.chdir(os.path.dirname(DD_DATA_DIR))
    data_dirname = os.path.basename(DD_DATA_DIR)  # Dumb-Panel

    # 本地备份目录放在数据目录外或内均可，这里默认放在 /app/Dumb-Panel/backups/
    backup_full_path = os.path.join(DD_DATA_DIR, DD_BACKUPS_PATH)
    mkdir(backup_full_path)

    now_time = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    files_name = f'{backup_full_path}/daidai-panel_{now_time}.tar.gz'

    logger.info(f'创建备份文件: {files_name}')
    if make_targz(files_name, data_dirname):
        logger.info('备份文件压缩完成...开始上传至阿里云盘')

        # 确保阿里云盘目录存在
        remote_folder = ali.get_folder_by_path(f'{DD_ALI_FOLDER}')
        if remote_folder is None:
            logger.info(f'阿里云盘目录 {DD_ALI_FOLDER} 不存在，尝试创建...')
            # 创建目录（在根目录下创建）
            remote_folder = ali.create_folder(DD_ALI_FOLDER)

        # 上传备份目录到阿里云盘
        ali.sync_folder(backup_full_path,
                        flag=True,
                        remote_folder=remote_folder.file_id)

        message_up_time = time.strftime(
            "%Y年%m月%d日 %H时%M分%S秒", time.localtime())
        text = f'已备份至阿里网盘:\n{files_name}\n' \
               f'\n备份完成时间:\n{message_up_time}\n' \
               f'\n呆呆面板数据备份完成！'
        try:
            send('【呆呆面板自动备份】', text)
        except:
            logger.info("通知发送失败")
        logger.info('---------------------备份完成---------------------')
    else:
        try:
            send('【呆呆面板自动备份】', '备份压缩失败,请检查日志')
        except:
            logger.info("通知发送失败")
        sys.exit(1)


def make_targz(output_filename, source_dir):
    """
    压缩为 tar.gz
    :param output_filename: 压缩文件名（绝对路径）
    :param source_dir: 源目录名（相对于当前工作目录）
    :return: bool
    """
    try:
        tar = tarfile.open(output_filename, "w:gz")

        # 遍历 Dumb-Panel 目录，排除指定目录
        for root, dirs, files in os.walk(source_dir):
            # 排除指定目录
            dirs[:] = [d for d in dirs if d not in DD_EXCLUDE_NAMES]

            for file in files:
                file_path = os.path.join(root, file)
                tar.add(file_path)

        tar.close()
        return True
    except Exception as e:
        logger.info(f'压缩失败: {str(e)}')
        return False


def mkdir(path):
    """创建备份目录"""
    folder = os.path.exists(path)
    if not folder:
        logger.info(f'第一次备份,创建备份目录: {path}')
        os.makedirs(path)
    else:
        # 检查备份文件数量
        files_all = [f for f in os.listdir(path) if f.endswith('.tar.gz')]
        files_num = len(files_all)
        logger.info(f'当前备份文件 {files_num}/{DD_MAX_FILES}')
        if files_num > DD_MAX_FILES:
            logger.info(f'达到最大备份数量 {DD_MAX_FILES} 个')
            check_files(files_all, files_num, path, DD_MAX_FILES)


def show(qr_link: str):
    """打印二维码链接"""
    logger.info('请手动复制以下链接，打开阿里网盘App扫描登录')
    logger.info(f'https://cli.im/api/qrcode/code?text={qr_link}')


def fileremove(filename):
    """删除旧的备份文件（本地 + 云端）"""
    if os.path.exists(filename):
        os.remove(filename)
        logger.info('已删除本地旧的备份文件: %s' % filename)

        # 获取云端文件
        remote_file = ali.get_file_by_path(
            os.path.join(DD_ALI_FOLDER, os.path.basename(filename))
        )
        if remote_file is not None:
            ali.move_file_to_trash(file_id=remote_file.file_id)
            logger.info('已删除云盘旧的备份文件: %s' % os.path.basename(filename))
        else:
            logger.info('未找到云端旧的备份文件: %s' % os.path.basename(filename))
    else:
        pass


def check_files(files_all, files_num, backup_files, max_files):
    """检查旧的备份文件"""
    create_time = []
    file_name = []
    for names in files_all:
        if names.endswith(".tar.gz"):
            filename = os.path.join(backup_files, names)
            file_name.append(filename)
            create_time.append(os.path.getctime(filename))

    dit = dict(zip(create_time, file_name))
    dit = sorted(dit.items(), key=lambda d: d[0], reverse=False)

    for i in range(files_num - max_files):
        file_location = dit[i][1]
        fileremove(file_location)


if __name__ == '__main__':
    nowtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    logger.info('---------' + str(nowtime) + ' 呆呆面板备份程序开始执行------------')

    # 呆呆面板数据目录检测
    if os.path.exists('/app/Dumb-Panel/'):
        logger.info('检测到呆呆面板数据目录 /app/Dumb-Panel/')
    else:
        logger.info('未检测到 /app/Dumb-Panel/，尝试当前目录...')
        if os.path.exists('./Dumb-Panel'):
            DD_DATA_DIR = os.path.abspath('./Dumb-Panel')
            logger.info(f'使用当前目录下的 Dumb-Panel: {DD_DATA_DIR}')
        else:
            logger.info('错误：未找到呆呆面板数据目录')
            try:
                send('【呆呆面板自动备份】', '未找到数据目录，备份失败')
            except:
                logger.info("通知发送失败")
            sys.exit(1)

    logger.info('登录阿里云盘')
    try:
        ali = Aligo(level=logging.INFO, show=show)
    except:
        logger.info('登录失败')
        try:
            send('【呆呆面板自动备份】', '阿里网盘登录失败,请手动重新运行本脚本登录')
        except:
            logger.info("通知发送失败")
        sys.exit(1)

    start()
    sys.exit(0)
