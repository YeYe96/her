Page({
    data: {
        simpleValue: '',
        clickCount: 0,
        chatValue: '',
        sendResult: '等待发送...'
    },

    onSimpleInput(e) {
        console.log('Simple input:', e.detail.value);
        this.setData({
            simpleValue: e.detail.value
        });
    },

    onTestClick() {
        console.log('Button clicked!');
        const count = this.data.clickCount + 1;
        this.setData({
            clickCount: count
        });
        wx.showToast({
            title: `第 ${count} 次点击`,
            icon: 'success'
        });
    },

    onChatInput(e) {
        console.log('Chat input:', e.detail.value);
        this.setData({
            chatValue: e.detail.value
        });
    },

    onSendTest() {
        console.log('Send clicked, value:', this.data.chatValue);
        if (!this.data.chatValue) {
            this.setData({
                sendResult: '❌ 请先输入内容'
            });
            return;
        }
        
        this.setData({
            sendResult: `✅ 已发送: ${this.data.chatValue}`,
            chatValue: ''
        });
        
        wx.showToast({
            title: '发送成功',
            icon: 'success'
        });
    },

    goBack() {
        wx.navigateBack();
    }
})
