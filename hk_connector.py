# coding=utf-8
import ctypes
import logging
import time
import traceback

from HCNetSDK import *
from PlayCtrl import *

logging.basicConfig(level=logging.INFO)


class HkConnector:
    def __init__(self):
        self.hikSDK, self.playM4SDK = self.load_sdk()  # 加载sdk库
        self.iUserID = -1  # 登录句柄
        self.lRealPlayHandle = -1  # 预览句柄
        self.FuncDecCB = None  # 解码回调
        self.PlayCtrlPort = C_LONG(-1)  # 播放通道号
        self.basePath = ''
        self.preview_file = ''
        self.funcRealDataCallBack_V30 = REALDATACALLBACK(self.RealDataCallBack_V30)  # 预览回调函数

    def load_sdk(self):
        hik_sdk = None
        play_m4_sdk = None
        try:
            hik_sdk = load_library(netsdkdllpath)
            play_m4_sdk = load_library(playM4dllpath)
        except OSError as e:
            logging.error(f"动态库加载失败: {str(e)} {traceback.format_exc()}")
        return hik_sdk, play_m4_sdk

    def init_dll(self):
        if sys_platform == 'windows':
            base_path = os.getcwd().encode('gbk')
            str_path = base_path + b'\\lib\\win'
            sdk_com_path = NET_DVR_LOCAL_SDK_PATH()
            sdk_com_path.sPath = str_path
            if self.hikSDK.NET_DVR_SetSDKInitCfg(NET_SDK_INIT_CFG_TYPE.NET_SDK_INIT_CFG_SDK_PATH.value, byref(sdk_com_path)):
                logging.info("NET_DVR_SetSDKInitCfg: 2 success.")
            else:
                logging.error("NET_DVR_SetSDKInitCfg: 2 failed!")
                return False
            if self.hikSDK.NET_DVR_SetSDKInitCfg(NET_SDK_INIT_CFG_TYPE.NET_SDK_INIT_CFG_LIBEAY_PATH.value, create_string_buffer(str_path + b'\\libcrypto-1_1-x64.dll')):
                logging.info("NET_DVR_SetSDKInitCfg: 3 success.")
            else:
                logging.error("NET_DVR_SetSDKInitCfg: 3 failed!")
                return False
            if self.hikSDK.NET_DVR_SetSDKInitCfg(NET_SDK_INIT_CFG_TYPE.NET_SDK_INIT_CFG_SSLEAY_PATH.value, create_string_buffer(str_path + b'\\libssl-1_1-x64.dll')):
                logging.info("NET_DVR_SetSDKInitCfg: 4 success.")
            else:
                logging.error("NET_DVR_SetSDKInitCfg: 4 failed!")
                return False
        else:
            base_path = os.getcwd().encode('utf-8')
            str_path = base_path + b'\\lib\\armlinux'
            sdk_com_path = NET_DVR_LOCAL_SDK_PATH()
            sdk_com_path.sPath = str_path
            if self.hikSDK.NET_DVR_SetSDKInitCfg(NET_SDK_INIT_CFG_TYPE.NET_SDK_INIT_CFG_SDK_PATH.value, byref(sdk_com_path)):
                logging.info("NET_DVR_SetSDKInitCfg: 2 success.")
            else:
                logging.error("NET_DVR_SetSDKInitCfg: 2 failed!")
                return False
            if self.hikSDK.NET_DVR_SetSDKInitCfg(NET_SDK_INIT_CFG_TYPE.NET_SDK_INIT_CFG_LIBEAY_PATH.value, create_string_buffer(str_path + b'/libcrypto.so.1.1')):
                logging.info("NET_DVR_SetSDKInitCfg: 3 success.")
            else:
                logging.error("NET_DVR_SetSDKInitCfg: 3 failed!")
                return False
            if self.hikSDK.NET_DVR_SetSDKInitCfg(NET_SDK_INIT_CFG_TYPE.NET_SDK_INIT_CFG_SSLEAY_PATH.value, create_string_buffer(str_path + b'/libssl.so.1.1')):
                logging.info("NET_DVR_SetSDKInitCfg: 4 success.")
            else:
                logging.error("NET_DVR_SetSDKInitCfg: 4 failed!")
                return False
        self.basePath = base_path
        return True

    def hk_log_setting(self):
        self.hikSDK.NET_DVR_SetLogToFile(3, bytes('./hk_sdk_log/', encoding="utf-8"), False)

    # 登录设备
    def login_dev(self, ip, username, pwd):
        # 登录参数，包括设备地址、登录用户、密码等
        strut_login_info = NET_DVR_USER_LOGIN_INFO()
        strut_login_info.bUseAsynLogin = 0  # 同步登录方式
        strut_login_info.sDeviceAddress = ip  # 设备IP地址
        strut_login_info.wPort = 8000  # 设备服务端口
        strut_login_info.sUserName = username  # 设备登录用户名
        strut_login_info.sPassword = pwd  # 设备登录密码
        strut_login_info.byLoginMode = 0

        # 设备信息, 输出参数
        strut_device_info_v40 = NET_DVR_DEVICEINFO_V40()

        self.iUserID = self.hikSDK.NET_DVR_Login_V40(byref(strut_login_info), byref(strut_device_info_v40))
        if self.iUserID < 0:
            logging.error(f"Login failed, error code: {str(self.hikSDK.NET_DVR_GetLastError())}")
            self.hikSDK.NET_DVR_Cleanup()
            return False
        else:
            logging.info(f"登录摄像头成功，设备序列号： {str(strut_device_info_v40.struDeviceV30.sSerialNumber, encoding="utf8").rstrip('\x00')}")
        return True

    def RealDataCallBack_V30(self, lPlayHandle, dwDataType, pBuffer, dwBufSize, pUser):
        if dwDataType == NET_DVR_SYSHEAD:
            # 设置流播放模式
            self.playM4SDK.PlayM4_SetStreamOpenMode(self.PlayCtrlPort, 0)
            # 打开码流，送入40字节系统头数据
            if self.playM4SDK.PlayM4_OpenStream(self.PlayCtrlPort, pBuffer, dwBufSize, 1024 * 1024):
                # 开始解码播放
                if self.playM4SDK.PlayM4_Play(self.PlayCtrlPort, None):
                    logging.info(f"播放库播放成功")
                else:
                    logging.error(f"播放库播放失败")
            else:
                logging.error(f'播放库打开流失败, 错误码：{str(self.playM4SDK.PlayM4_GetLastError(self.PlayCtrlPort))}')
        elif dwDataType == NET_DVR_STREAMDATA:
            self.playM4SDK.PlayM4_InputData(self.PlayCtrlPort, pBuffer, dwBufSize)
        else:
            pass

    def get_frame(self):
        p_width = ctypes.c_int(0)
        p_height = ctypes.c_int(0)
        if not self.playM4SDK.PlayM4_GetPictureSize(self.PlayCtrlPort, ctypes.byref(p_width), ctypes.byref(p_height)):
            logging.error(f'获取PlayM4_GetPictureSize失败, 错误码：{str(self.playM4SDK.PlayM4_GetLastError(self.PlayCtrlPort))}')
        print(f"PlayM4_GetPictureSize value: {p_width.value}, {p_height.value}")
        pic_buff_size = p_width.value * p_height.value * 5
        jpeg_buffer = (ctypes.c_ubyte * pic_buff_size)()
        real_pic_size = ctypes.c_int(0)
        result = self.playM4SDK.PlayM4_GetJPEG(self.PlayCtrlPort, jpeg_buffer, pic_buff_size, ctypes.byref(real_pic_size))

        pic_bits = None
        if result == 1:
            pic_bits = bytes(jpeg_buffer[:real_pic_size.value])
            # 保存为 JPEG 文件
            img_filename = f'pic/image_{time.time()}.jpg'
            with open(img_filename, 'wb') as f:
                f.write(pic_bits)
        else:
            logging.error(f'抓图PlayM4_GetJPEG失败, 错误码：{str(self.playM4SDK.PlayM4_GetLastError(self.PlayCtrlPort))}')

        return pic_bits

    def start_play(self):
        # 获取一个播放句柄
        if not self.playM4SDK.PlayM4_GetPort(byref(self.PlayCtrlPort)):
            logging.error(f'获取播放库句柄失败, 错误码：{str(self.playM4SDK.PlayM4_GetLastError(self.PlayCtrlPort))}')
            return False

        # 开始预览
        preview_info = NET_DVR_PREVIEWINFO()
        preview_info.hPlayWnd = 0
        preview_info.lChannel = 1  # 通道号
        preview_info.dwStreamType = 0  # 主码流
        preview_info.dwLinkMode = 0  # TCP
        preview_info.bBlocked = 1  # 阻塞取流

        # 开始预览并且设置回调函数回调获取实时流数据
        self.lRealPlayHandle = self.hikSDK.NET_DVR_RealPlay_V40(self.iUserID, byref(preview_info), self.funcRealDataCallBack_V30, None)
        if self.lRealPlayHandle < 0:
            logging.error(f"Open preview failed, error code: {str(self.hikSDK.NET_DVR_GetLastError())}")
            # 登出设备
            self.hikSDK.NET_DVR_Logout(self.iUserID)
            # 释放资源
            self.hikSDK.NET_DVR_Cleanup()
            return False

        return True


if __name__ == '__main__':
    dev = HkConnector()
    dev.init_dll()  # 设置SDK初始化依赖库路径
    dev.hikSDK.NET_DVR_Init()  # 初始化sdk
    dev.hk_log_setting()  # 通用设置，日志，回调函数等
    dev.login_dev(ip=b'169.254.43.56', username=b"admin", pwd=b"tongda2024")  # 登录设备
    dev.start_play()
    time.sleep(5)
    dev.get_frame()
    time.sleep(20)
