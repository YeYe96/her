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

        // 视觉系统状态
        visual: {
            scene: '', // 背景图 (动态加载)
            character: {
                body: '',
                opacity: 1.0,
                scale: 1.0
            },
            filter: 'none'
        },

        // UI 状态
        showMorePanel: false
    },

    onLoad() {
        this.ctx = wx.createCameraContext();

        // 动态加载背景图 (解决 2MB 包大小限制)
        const baseUrl = app.globalData.baseUrl;
        this.setData({
            'visual.scene': `${baseUrl}/static/character/kurisu.png`
        });
    },

    // 切换更多功能面板
    toggleMorePanel() {
        const isOpening = !this.data.showMorePanel;
        this.setData({
            showMorePanel: isOpening,
            inputFocus: false
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
        const type = e.currentTarget.dataset.type;
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

    // 发送图片消息
    sendImageMessage(tempFilePath) {
        const newMsg = {
            id: Date.now(),
            role: 'user',
            content: '[图片]',
            image: tempFilePath
        };
        this.updateMessages(newMsg);

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
            showMorePanel: false
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
                title: '请输入消息',
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
            inputValue: '',
            toView: `msg-${messages.length - 1}`
        });
    },

    callBackend(text, imageBase64) {
        // 显示思考状态
        this.updateCharacterEmotion('thinking');

        wx.request({
            url: `${app.globalData.baseUrl}/chat`,
            method: 'POST',
            timeout: 120000, // 2分钟超时
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

                this.analyzeEmotionFromReply(res.data.reply || '');
            },
            fail: (err) => {
                console.error(err);
                const errMsg = { id: Date.now(), role: 'amadeus', content: '连接错误，后端是否运行？' };
                this.setData({
                    messages: this.data.messages.concat(errMsg)
                });
                this.updateCharacterEmotion('normal');
            }
        })
    },

    // 更新角色情绪
    updateCharacterEmotion(emotion) {
        switch (emotion) {
            case 'thinking':
                this.setData({
                    'visual.character.opacity': 0.8,
                    'visual.filter': 'blur(1px) brightness(0.9)'
                });
                break;
            case 'happy':
                this.setData({
                    'visual.character.opacity': 1.0,
                    'visual.filter': 'brightness(1.1)'
                });
                break;
            default:
                this.setData({
                    'visual.character.opacity': 1.0,
                    'visual.filter': 'none'
                });
        }
    },

    // 简单回复情绪分析
    analyzeEmotionFromReply(reply) {
        const content = reply.toLowerCase();
        if (content.includes('哼') || content.includes('才不是')) {
            this.updateCharacterEmotion('happy');
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
