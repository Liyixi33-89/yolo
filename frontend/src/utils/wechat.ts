/**
 * 微信 JS-SDK 工具类
 * 用于在微信内置浏览器中调用原生录音、摄像头等功能
 */

// 微信 JS-SDK 类型声明
declare global {
  interface Window {
    wx?: WechatJSSDK;
  }
}

interface WechatJSSDK {
  config: (config: WxConfig) => void;
  ready: (callback: () => void) => void;
  error: (callback: (res: { errMsg: string }) => void) => void;
  // 录音相关
  startRecord: () => void;
  stopRecord: (options: {
    success: (res: { localId: string }) => void;
    fail?: (res: { errMsg: string }) => void;
  }) => void;
  uploadVoice: (options: {
    localId: string;
    isShowProgressTips: number;
    success: (res: { serverId: string }) => void;
    fail?: (res: { errMsg: string }) => void;
  }) => void;
  downloadVoice: (options: {
    serverId: string;
    isShowProgressTips: number;
    success: (res: { localId: string }) => void;
    fail?: (res: { errMsg: string }) => void;
  }) => void;
  playVoice: (options: { localId: string }) => void;
  stopVoice: (options: { localId: string }) => void;
  onVoiceRecordEnd: (options: {
    complete: (res: { localId: string }) => void;
  }) => void;
  // 图片相关
  chooseImage: (options: {
    count?: number;
    sizeType?: string[];
    sourceType?: string[];
    success: (res: { localIds: string[] }) => void;
    fail?: (res: { errMsg: string }) => void;
  }) => void;
  getLocalImgData: (options: {
    localId: string;
    success: (res: { localData: string }) => void;
    fail?: (res: { errMsg: string }) => void;
  }) => void;
  uploadImage: (options: {
    localId: string;
    isShowProgressTips: number;
    success: (res: { serverId: string }) => void;
    fail?: (res: { errMsg: string }) => void;
  }) => void;
  // 权限检查
  checkJsApi: (options: {
    jsApiList: string[];
    success: (res: { checkResult: Record<string, boolean> }) => void;
  }) => void;
}

interface WxConfig {
  debug?: boolean;
  appId: string;
  timestamp: number;
  nonceStr: string;
  signature: string;
  jsApiList: string[];
}

interface WxSignatureResponse {
  success: boolean;
  data?: {
    appId: string;
    timestamp: number;
    nonceStr: string;
    signature: string;
  };
  error?: string;
}

/**
 * 检测是否在微信浏览器中
 */
export const isWechatBrowser = (): boolean => {
  const ua = navigator.userAgent.toLowerCase();
  return ua.includes('micromessenger');
};

/**
 * 检测是否支持标准的 getUserMedia API
 */
export const isGetUserMediaSupported = (): boolean => {
  return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
};

/**
 * 检测是否在安全上下文中（HTTPS 或 localhost）
 */
export const isSecureContext = (): boolean => {
  return window.isSecureContext || 
         location.protocol === 'https:' || 
         location.hostname === 'localhost' || 
         location.hostname === '127.0.0.1';
};

/**
 * 获取录音能力类型
 */
export type RecordingCapability = 'standard' | 'wechat' | 'none';

export const getRecordingCapability = (): RecordingCapability => {
  // 微信环境优先使用微信 SDK
  if (isWechatBrowser()) {
    return 'wechat';
  }
  
  // 非微信环境，检查是否支持标准 API
  if (isSecureContext() && isGetUserMediaSupported()) {
    return 'standard';
  }
  
  return 'none';
};

/**
 * 获取摄像头能力类型
 */
export type CameraCapability = 'standard' | 'wechat' | 'none';

export const getCameraCapability = (): CameraCapability => {
  // 微信环境优先使用微信 SDK
  if (isWechatBrowser()) {
    return 'wechat';
  }
  
  // 非微信环境，检查是否支持标准 API
  if (isSecureContext() && isGetUserMediaSupported()) {
    return 'standard';
  }
  
  return 'none';
};

/**
 * 加载微信 JS-SDK
 */
export const loadWechatSDK = (): Promise<void> => {
  return new Promise((resolve, reject) => {
    if (window.wx) {
      resolve();
      return;
    }

    const script = document.createElement('script');
    script.src = 'https://res.wx.qq.com/open/js/jweixin-1.6.0.js';
    script.onload = () => resolve();
    script.onerror = () => reject(new Error('微信 SDK 加载失败'));
    document.head.appendChild(script);
  });
};

/**
 * 微信 SDK 初始化状态
 */
let wechatSDKInitialized = false;
let wechatSDKInitializing = false;
let wechatSDKInitPromise: Promise<boolean> | null = null;

/**
 * 初始化微信 JS-SDK
 * 注意：需要后端提供签名接口
 */
export const initWechatSDK = async (): Promise<boolean> => {
  // 如果已初始化，直接返回
  if (wechatSDKInitialized) {
    return true;
  }
  
  // 如果正在初始化，等待结果
  if (wechatSDKInitializing && wechatSDKInitPromise) {
    return wechatSDKInitPromise;
  }
  
  wechatSDKInitializing = true;
  
  wechatSDKInitPromise = (async () => {
    try {
      await loadWechatSDK();

      // 从后端获取签名
      const response = await fetch('/api/wechat/signature', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: window.location.href.split('#')[0] }),
      });

      const result: WxSignatureResponse = await response.json();
      
      if (!result.success || !result.data) {
        console.error('获取微信签名失败:', result.error);
        wechatSDKInitializing = false;
        return false;
      }

      return new Promise<boolean>((resolve) => {
        window.wx?.config({
          debug: false,
          appId: result.data!.appId,
          timestamp: result.data!.timestamp,
          nonceStr: result.data!.nonceStr,
          signature: result.data!.signature,
          jsApiList: [
            // 录音相关
            'startRecord',
            'stopRecord',
            'uploadVoice',
            'downloadVoice',
            'playVoice',
            'stopVoice',
            'onVoiceRecordEnd',
            // 图片/摄像头相关
            'chooseImage',
            'getLocalImgData',
            'uploadImage',
            // 权限检查
            'checkJsApi',
          ],
        });

        window.wx?.ready(() => {
          console.log('微信 SDK 初始化成功');
          wechatSDKInitialized = true;
          wechatSDKInitializing = false;
          resolve(true);
        });

        window.wx?.error((res) => {
          console.error('微信 SDK 初始化失败:', res.errMsg);
          wechatSDKInitializing = false;
          resolve(false);
        });
      });
    } catch (error) {
      console.error('微信 SDK 初始化异常:', error);
      wechatSDKInitializing = false;
      return false;
    }
  })();
  
  return wechatSDKInitPromise;
};

/**
 * 检查微信 API 是否可用
 */
export const checkWechatApi = (apiList: string[]): Promise<Record<string, boolean>> => {
  return new Promise((resolve) => {
    if (!window.wx) {
      const result: Record<string, boolean> = {};
      apiList.forEach(api => result[api] = false);
      resolve(result);
      return;
    }
    
    window.wx.checkJsApi({
      jsApiList: apiList,
      success: (res) => {
        resolve(res.checkResult);
      }
    });
  });
};

/**
 * 微信录音类
 */
export class WechatRecorder {
  private _localId: string | null = null;
  private isRecording = false;
  private onRecordEnd?: (localId: string) => void;

  // 获取最后录音的 localId
  get localId(): string | null {
    return this._localId;
  }

  constructor() {
    // 监听录音自动停止事件（超过60秒会自动停止）
    if (window.wx) {
      window.wx.onVoiceRecordEnd({
        complete: (res) => {
          this._localId = res.localId;
          this.isRecording = false;
          this.onRecordEnd?.(res.localId);
        },
      });
    }
  }

  /**
   * 开始录音
   */
  start(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!window.wx) {
        reject(new Error('微信 SDK 未加载'));
        return;
      }

      try {
        window.wx.startRecord();
        this.isRecording = true;
        resolve();
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * 停止录音
   */
  stop(): Promise<string> {
    return new Promise((resolve, reject) => {
      if (!window.wx) {
        reject(new Error('微信 SDK 未加载'));
        return;
      }

      window.wx.stopRecord({
        success: (res) => {
          this._localId = res.localId;
          this.isRecording = false;
          resolve(res.localId);
        },
        fail: (res) => {
          reject(new Error(res.errMsg));
        },
      });
    });
  }

  /**
   * 上传录音到微信服务器
   */
  upload(localId: string): Promise<string> {
    return new Promise((resolve, reject) => {
      if (!window.wx) {
        reject(new Error('微信 SDK 未加载'));
        return;
      }

      window.wx.uploadVoice({
        localId,
        isShowProgressTips: 1,
        success: (res) => {
          resolve(res.serverId);
        },
        fail: (res) => {
          reject(new Error(res.errMsg));
        },
      });
    });
  }

  /**
   * 播放录音
   */
  play(localId: string): void {
    window.wx?.playVoice({ localId });
  }

  /**
   * 停止播放
   */
  stopPlay(localId: string): void {
    window.wx?.stopVoice({ localId });
  }

  /**
   * 设置录音结束回调
   */
  setOnRecordEnd(callback: (localId: string) => void): void {
    this.onRecordEnd = callback;
  }

  /**
   * 获取录音状态
   */
  getIsRecording(): boolean {
    return this.isRecording;
  }
}

/**
 * 微信图片选择器类
 * 用于在微信环境中选择图片（相册或摄像头）
 */
export class WechatImagePicker {
  /**
   * 选择图片
   * @param sourceType 来源类型：'album' 相册, 'camera' 摄像头, 'both' 两者都可
   * @param count 选择数量，默认1
   */
  static choose(sourceType: 'album' | 'camera' | 'both' = 'both', count: number = 1): Promise<string[]> {
    return new Promise((resolve, reject) => {
      if (!window.wx) {
        reject(new Error('微信 SDK 未加载'));
        return;
      }
      
      const source: string[] = [];
      if (sourceType === 'album' || sourceType === 'both') {
        source.push('album');
      }
      if (sourceType === 'camera' || sourceType === 'both') {
        source.push('camera');
      }

      window.wx.chooseImage({
        count,
        sizeType: ['original', 'compressed'],
        sourceType: source,
        success: (res) => {
          resolve(res.localIds);
        },
        fail: (res) => {
          reject(new Error(res.errMsg));
        },
      });
    });
  }

  /**
   * 获取本地图片的 base64 数据
   * @param localId 本地图片ID
   */
  static getBase64(localId: string): Promise<string> {
    return new Promise((resolve, reject) => {
      if (!window.wx) {
        reject(new Error('微信 SDK 未加载'));
        return;
      }

      window.wx.getLocalImgData({
        localId,
        success: (res) => {
          // 微信返回的数据格式: data:image/jpeg;base64,xxx 或 iOS 下可能是 weixin://xxx
          let base64Data = res.localData;
          
          // 处理 iOS 下的特殊格式
          if (base64Data.indexOf('data:image') !== 0) {
            // iOS 下需要手动添加头部
            base64Data = 'data:image/jpeg;base64,' + base64Data;
          }
          
          // 处理 Android 下可能出现的换行符
          base64Data = base64Data.replace(/\r|\n/g, '');
          
          resolve(base64Data);
        },
        fail: (res) => {
          reject(new Error(res.errMsg));
        },
      });
    });
  }

  /**
   * 上传图片到微信服务器
   * @param localId 本地图片ID
   */
  static upload(localId: string): Promise<string> {
    return new Promise((resolve, reject) => {
      if (!window.wx) {
        reject(new Error('微信 SDK 未加载'));
        return;
      }

      window.wx.uploadImage({
        localId,
        isShowProgressTips: 1,
        success: (res) => {
          resolve(res.serverId);
        },
        fail: (res) => {
          reject(new Error(res.errMsg));
        },
      });
    });
  }

  /**
   * 选择图片并获取 base64（便捷方法）
   * @param sourceType 来源类型
   */
  static async chooseAndGetBase64(sourceType: 'album' | 'camera' | 'both' = 'both'): Promise<string | null> {
    try {
      const localIds = await this.choose(sourceType, 1);
      if (localIds.length > 0) {
        return await this.getBase64(localIds[0]);
      }
      return null;
    } catch (error) {
      console.error('选择图片失败:', error);
      throw error;
    }
  }
}

/**
 * 获取录音环境提示信息
 */
export const getRecordingTip = (): string => {
  const capability = getRecordingCapability();
  
  switch (capability) {
    case 'standard':
      return '点击开始录音';
    case 'wechat':
      return '点击开始录音（微信环境）';
    case 'none':
      if (!isSecureContext()) {
        return '⚠️ 录音功能需要 HTTPS 环境';
      }
      return '⚠️ 当前浏览器不支持录音';
  }
};

/**
 * 获取摄像头环境提示信息
 */
export const getCameraTip = (): string => {
  const capability = getCameraCapability();
  
  switch (capability) {
    case 'standard':
      return '点击拍照';
    case 'wechat':
      return '点击拍照（微信环境）';
    case 'none':
      if (!isSecureContext()) {
        return '⚠️ 摄像头功能需要 HTTPS 环境';
      }
      return '⚠️ 当前浏览器不支持摄像头';
  }
};
