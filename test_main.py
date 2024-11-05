# coding=utf-8
import ctypes
import time

from HCNetSDK import *
from PlayCtrl import *


class devClass:
    def __init__(self):
        self.hikSDK, self.playM4SDK = self.LoadSDK()  # 加载sdk库
        self.iUserID = -1  # 登录句柄
        self.lRealPlayHandle = -1  # 预览句柄
        self.FuncDecCB = None  # 解码回调
        self.PlayCtrlPort = C_LONG(-1)  # 播放通道号
        self.basePath = ''
        self.preview_file = ''
        self.funcRealDataCallBack_V30 = REALDATACALLBACK(self.RealDataCallBack_V30)  # 预览回调函数

    def LoadSDK(self):
        hikSDK = None
        playM4SDK = None
        try:
            hikSDK = load_library(netsdkdllpath)
            playM4SDK = load_library(playM4dllpath)
        except OSError as e:
            print('动态库加载失败', e)
        return hikSDK, playM4SDK

    def SetSDKInitCfg(self):
        if sys_platform == 'windows':
            basePath = os.getcwd().encode('gbk')
            strPath = basePath + b'\\lib\\win'
            sdk_ComPath = NET_DVR_LOCAL_SDK_PATH()
            sdk_ComPath.sPath = strPath
            print('strPath: ', strPath)
            if self.hikSDK.NET_DVR_SetSDKInitCfg(NET_SDK_INIT_CFG_TYPE.NET_SDK_INIT_CFG_SDK_PATH.value,
                                                 byref(sdk_ComPath)):
                print('NET_DVR_SetSDKInitCfg: 2 Succ')
            if self.hikSDK.NET_DVR_SetSDKInitCfg(NET_SDK_INIT_CFG_TYPE.NET_SDK_INIT_CFG_LIBEAY_PATH.value,
                                                 create_string_buffer(strPath + b'\\libcrypto-1_1-x64.dll')):
                print('NET_DVR_SetSDKInitCfg: 3 Succ')
            if self.hikSDK.NET_DVR_SetSDKInitCfg(NET_SDK_INIT_CFG_TYPE.NET_SDK_INIT_CFG_SSLEAY_PATH.value,
                                                 create_string_buffer(strPath + b'\\libssl-1_1-x64.dll')):
                print('NET_DVR_SetSDKInitCfg: 4 Succ')
        else:
            basePath = os.getcwd().encode('utf-8')
            strPath = basePath + b'\\lib\\armlinux'
            sdk_ComPath = NET_DVR_LOCAL_SDK_PATH()
            sdk_ComPath.sPath = strPath
            if self.hikSDK.NET_DVR_SetSDKInitCfg(NET_SDK_INIT_CFG_TYPE.NET_SDK_INIT_CFG_SDK_PATH.value,
                                                 byref(sdk_ComPath)):
                print('NET_DVR_SetSDKInitCfg: 2 Succ')
            if self.hikSDK.NET_DVR_SetSDKInitCfg(NET_SDK_INIT_CFG_TYPE.NET_SDK_INIT_CFG_LIBEAY_PATH.value,
                                                 create_string_buffer(strPath + b'/libcrypto.so.1.1')):
                print('NET_DVR_SetSDKInitCfg: 3 Succ')
            if self.hikSDK.NET_DVR_SetSDKInitCfg(NET_SDK_INIT_CFG_TYPE.NET_SDK_INIT_CFG_SSLEAY_PATH.value,
                                                 create_string_buffer(strPath + b'/libssl.so.1.1')):
                print('NET_DVR_SetSDKInitCfg: 4 Succ')
        self.basePath = basePath

    def GeneralSetting(self):
        self.hikSDK.NET_DVR_SetLogToFile(3, bytes('./SdkLog_Python/', encoding="utf-8"), False)

    # 登录设备
    def LoginDev(self, ip, username, pwd):
        # 登录参数，包括设备地址、登录用户、密码等
        struLoginInfo = NET_DVR_USER_LOGIN_INFO()
        struLoginInfo.bUseAsynLogin = 0  # 同步登录方式
        struLoginInfo.sDeviceAddress = ip  # 设备IP地址
        struLoginInfo.wPort = 8000  # 设备服务端口
        struLoginInfo.sUserName = username  # 设备登录用户名
        struLoginInfo.sPassword = pwd  # 设备登录密码
        struLoginInfo.byLoginMode = 0

        # 设备信息, 输出参数
        struDeviceInfoV40 = NET_DVR_DEVICEINFO_V40()

        self.iUserID = self.hikSDK.NET_DVR_Login_V40(byref(struLoginInfo), byref(struDeviceInfoV40))
        if self.iUserID < 0:
            print("Login failed, error code: %d" % self.hikSDK.NET_DVR_GetLastError())
            self.hikSDK.NET_DVR_Cleanup()
        else:
            print('登录成功，设备序列号：%s' % str(struDeviceInfoV40.struDeviceV30.sSerialNumber, encoding="utf8").rstrip('\x00'))


    def RealDataCallBack_V30(self, lPlayHandle, dwDataType, pBuffer, dwBufSize, pUser):
        if dwDataType == NET_DVR_SYSHEAD:
            # 设置流播放模式
            self.playM4SDK.PlayM4_SetStreamOpenMode(self.PlayCtrlPort, 0)
            # 打开码流，送入40字节系统头数据
            if self.playM4SDK.PlayM4_OpenStream(self.PlayCtrlPort, pBuffer, dwBufSize, 1024 * 1024):
                # 开始解码播放
                if self.playM4SDK.PlayM4_Play(self.PlayCtrlPort, None):
                    print(u'播放库播放成功')
                else:
                    print(u'播放库播放失败')
            else:
                print(f'播放库打开流失败, 错误码：{self.playM4SDK.PlayM4_GetLastError(self.PlayCtrlPort)}')
        elif dwDataType == NET_DVR_STREAMDATA:
            self.playM4SDK.PlayM4_InputData(self.PlayCtrlPort, pBuffer, dwBufSize)

            p_width = ctypes.c_int(0)
            p_height = ctypes.c_int(0)
            if not self.playM4SDK.PlayM4_GetPictureSize(self.PlayCtrlPort, ctypes.byref(p_width),
                                                        ctypes.byref(p_height)):
                print(f'获取PlayM4_GetPictureSize失败, 错误码：{self.playM4SDK.PlayM4_GetLastError(self.PlayCtrlPort)}')
            print(f"PlayM4_GetPictureSize value: {p_width.value}, {p_height.value}")

            pic_buff_size = p_width.value * p_height.value * 5
            jpeg_buffer = (ctypes.c_ubyte * pic_buff_size)()
            real_pic_size = ctypes.c_int(0)
            result = self.playM4SDK.PlayM4_GetJPEG(self.PlayCtrlPort, jpeg_buffer, pic_buff_size,
                                                   ctypes.byref(real_pic_size))
            if result == 1:
                print(f"PlayM4_GetJPEG value: {real_pic_size.value}")

                # 保存为 JPEG 文件
                img_filename = f'pic/image_{time.time()}.jpg'
                with open(img_filename, 'wb') as f:
                    f.write(bytes(jpeg_buffer[:real_pic_size.value]))

            else:
                print(f'抓图PlayM4_GetJPEG失败, 错误码：{self.playM4SDK.PlayM4_GetLastError(self.PlayCtrlPort)}')
        else:
            print(u'其他数据,长度:', dwBufSize)


    def start_play(self):
        # 获取一个播放句柄
        if not self.playM4SDK.PlayM4_GetPort(byref(self.PlayCtrlPort)):
            print(f'获取播放库句柄失败, 错误码：{self.playM4SDK.PlayM4_GetLastError(self.PlayCtrlPort)}')

        # 开始预览
        preview_info = NET_DVR_PREVIEWINFO()
        preview_info.hPlayWnd = 0
        preview_info.lChannel = 1  # 通道号
        preview_info.dwStreamType = 0  # 主码流
        preview_info.dwLinkMode = 0  # TCP
        preview_info.bBlocked = 1  # 阻塞取流

        # 开始预览并且设置回调函数回调获取实时流数据
        self.lRealPlayHandle = self.hikSDK.NET_DVR_RealPlay_V40(self.iUserID, byref(preview_info),
                                                                self.funcRealDataCallBack_V30,
                                                                None)
        if self.lRealPlayHandle < 0:
            print('Open preview fail, error code is: %d' % self.hikSDK.NET_DVR_GetLastError())
            # 登出设备
            self.hikSDK.NET_DVR_Logout(self.iUserID)
            # 释放资源
            self.hikSDK.NET_DVR_Cleanup()
            exit()


if __name__ == '__main__':
    dev = devClass()
    dev.SetSDKInitCfg()  # 设置SDK初始化依赖库路径
    dev.hikSDK.NET_DVR_Init()  # 初始化sdk
    dev.GeneralSetting()  # 通用设置，日志，回调函数等
    dev.LoginDev(ip=b'169.254.43.56', username=b"admin", pwd=b"tongda2024")  # 登录设备

    dev.start_play()  # playTime用于linux环境控制预览时长，windows环境无效
    time.sleep(20)
