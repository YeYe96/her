App({
    onLaunch() {
        console.log('Amadeus System Launching...');
    },
    globalData: {
        userInfo: null,
        // 局域网 IP（手机和电脑需在同一 Wi-Fi）
        // 如需 Tailscale 访问，改为: http://100.95.173.128:8003
        baseUrl: 'http://192.168.31.216:8003' // Local network URL
    }
})
