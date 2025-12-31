/**
 * 微信 JS-SDK 工具类
 * 用于在微信内置浏览器中调用原生录音功能
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
 * 初始化微信 JS-SDK
 * 注意：需要后端提供签名接口
 */
export const initWechatSDK = async (): Promise<boolean> => {
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
      return false;
    }

    return new Promise((resolve) => {
      window.wx?.config({
        debug: false,
        appId: result.data!.appId,
        timestamp: result.data!.timestamp,
        nonceStr: result.data!.nonceStr,
        signature: result.data!.signature,
        jsApiList: [
          'startRecord',
          'stopRecord',
          'uploadVoice',
          'downloadVoice',
          'playVoice',
          'stopVoice',
          'onVoiceRecordEnd',
        ],
      });

      window.wx?.ready(() => {
        console.log('微信 SDK 初始化成功');
        resolve(true);
      });

      window.wx?.error((res) => {
        console.error('微信 SDK 初始化失败:', res.errMsg);
        resolve(false);
      });
    });
  } catch (error) {
    console.error('微信 SDK 初始化异常:', error);
    return false;
  }
};

/**
 * 微信录音类
 */
export class WechatRecorder {
  private localId: string | null = null;
  private isRecording = false;
  private onRecordEnd?: (localId: string) => void;

  constructor() {
    // 监听录音自动停止事件（超过60秒会自动停止）
    if (window.wx) {
      window.wx.onVoiceRecordEnd({
        complete: (res) => {
          this.localId = res.localId;
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
          this.localId = res.localId;
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
