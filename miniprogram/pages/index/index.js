const app = getApp()

Page({
    data: {
        messages: [
            { id: 0, role: 'amadeus', content: 'Amadeus System Initialized. Waiting for input.' }
        ],
        inputValue: '',
        showCamera: false,
        toView: 'msg-0',
        inputFocus: false,
        // 角色状态（用于后续的情绪展示）
        characterEmotion: 'normal', // normal, happy, thinking, surprised, etc.
        characterOpacity: 1.0,
        characterFilter: 'blur(2px)',

        // 新增 UI 状态
        showMorePanel: false // 是否显示更多功能面板
    },

    onLoad() {
        this.ctx = wx.createCameraContext()
    },

    // 切换 (+) 更多功能面板的显示/隐藏
    toggleMorePanel() {
        const isOpening = !this.data.showMorePanel;
        this.setData({
            showMorePanel: isOpening,
            inputFocus: false // 打开面板时收起键盘
        });

        if (isOpening) {
            this.scrollToBottom();
        }
    },

    // 表情功能占位符
    toggleEmoji() {
        wx.showToast({
            title: '表情功能开发中',
            icon: 'none'
        });
    },

    // 点击聊天区域关闭面板
    closePanels() {
        if (this.data.showMorePanel) {
            this.setData({ showMorePanel: false });
        }
    },

    // 处理媒体选择 (相册/相机)
    handleChooseMedia(e) {
        const type = e.currentTarget.dataset.type; // 'image' 或 'camera'
        const sourceType = type === 'camera' ? ['camera'] : ['album'];

        wx.chooseMedia({
            count: 1,
            mediaType: ['image'],
            sourceType: sourceType,
            camera: 'back',
            success: (res) => {
                const tempFilePath = res.tempFiles[0].tempFilePath;
                this.sendImageMessage(tempFilePath);
                this.setData({ showMorePanel: false });
            }
        });
    },

    // 视频通话占位符
    handleVideoCall() {
        wx.showToast({
            title: '视频通话功能正在接入',
            icon: 'none'
        });
        this.setData({ showMorePanel: false });
    },

    // 发送图片消息逻辑
    sendImageMessage(tempFilePath) {
        const newMsg = {
            id: Date.now(),
            role: 'user',
            content: '[图片]',
            image: tempFilePath
        };
        this.updateMessages(newMsg);

        // 读取文件并发送给后端
        wx.getFileSystemManager().readFile({
            filePath: tempFilePath,
            encoding: 'base64',
            success: (data) => {
                this.callBackend('', data.data);
            }
        });
    },

    handleInput(e) {
        this.setData({
            inputValue: e.detail.value
        });
    },

    onInputFocus(e) {
        this.setData({
            inputFocus: true,
            showMorePanel: false // 键盘弹出时关闭功能面板
        });
        this.scrollToBottom();
    },

    scrollToBottom() {
        setTimeout(() => {
            const messages = this.data.messages;
            if (messages.length > 0) {
                this.setData({
                    toView: `msg-${messages.length - 1}`
                });
            }
        }, 100);
    },

    sendMessage() {
        const content = this.data.inputValue;
        if (!content) {
            wx.showToast({
                title: 'Cannot send empty message',
                icon: 'none'
            });
            return;
        }

        const newMsg = { id: Date.now(), role: 'user', content };
        this.updateMessages(newMsg);
        this.callBackend(content, null);
    },

    updateMessages(newMsg) {
        const messages = this.data.messages.concat(newMsg);
        this.setData({
            messages,
            inputValue: '', // 清空输入框
            toView: `msg-${messages.length - 1}`
        });
    },

    callBackend(text, imageBase64) {
        // 发送消息时，显示"思考"状态
        this.updateCharacterEmotion('thinking');

        wx.request({
            url: `${app.globalData.baseUrl}/chat`,
            method: 'POST',
            data: {
                text: text,
                image_base64: imageBase64
            },
            success: (res) => {
                const reply = { id: Date.now(), role: 'amadeus', content: res.data.reply || '...' };
                this.setData({
                    messages: this.data.messages.concat(reply),
                    toView: `msg-${this.data.messages.length}`
                });

                // 根据回复内容分析情绪
                this.analyzeEmotionFromReply(res.data.reply || '');
            },
            fail: (err) => {
                console.error(err);
                const errMsg = { id: Date.now(), role: 'amadeus', content: 'Connection Error. Is Backend Running?' };
                this.setData({
                    messages: this.data.messages.concat(errMsg)
                });
                this.updateCharacterEmotion('normal');
            }
        })
    },

    // 语音录制相关 (已移除)

    // 更新角色情绪
    updateCharacterEmotion(emotion) {
        this.setData({
            characterEmotion: emotion
        });
        switch (emotion) {
            case 'thinking':
                this.setData({ characterOpacity: 0.8, characterFilter: 'blur(1px) brightness(0.9)' });
                break;
            case 'happy':
                this.setData({ characterOpacity: 1.0, characterFilter: 'blur(1px) brightness(1.1)' });
                break;
            case 'surprised':
                this.setData({ characterOpacity: 0.9, characterFilter: 'blur(0px) brightness(1.05)' });
                break;
            default:
                this.setData({ characterOpacity: 1.0, characterFilter: 'blur(2px)' });
        }
    },

    // 简单回复情绪分析
    analyzeEmotionFromReply(reply) {
        const content = reply.toLowerCase();
        if (content.includes('哼') || content.includes('才不是')) {
            this.updateCharacterEmotion('happy');
        } else if (content.includes('？') || content.includes('?') || content.includes('什么')) {
            this.updateCharacterEmotion('surprised');
        } else {
            this.updateCharacterEmotion('normal');
        }
        setTimeout(() => {
            this.updateCharacterEmotion('normal');
        }, 3000);
    },

    error(e) {
        console.log(e.detail);
    }
})
