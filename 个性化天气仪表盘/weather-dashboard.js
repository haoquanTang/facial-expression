/**
 * 个性化天气仪表盘 - 主要JavaScript文件
 * 实现天气数据获取、可视化图表、自定义仪表盘等功能
 */

const { createApp } = Vue;

createApp({
    data() {
        return {
            // 基础数据
            isLoading: false,
            currentLocation: '',
            searchCity: '',
            
            // 当前天气数据
            currentWeather: {
                temperature: '--',
                feelsLike: '--',
                description: '获取中...',
                icon: '',
                humidity: '--',
                windSpeed: '--',
                visibility: '--',
                pressure: '--'
            },
            
            // 7天预报数据
            forecastData: [],
            
            // 图表相关
            chartType: 'temperature',
            weatherChart: null,
            
            // 仪表盘组件
            showComponentSelector: false,
            activeComponents: [],
            availableComponents: [
                { id: 'air-quality', name: '空气质量', icon: 'fas fa-leaf' },
                { id: 'uv-index', name: '紫外线指数', icon: 'fas fa-sun' },
                { id: 'precipitation', name: '降水概率', icon: 'fas fa-cloud-rain' },
                { id: 'clothing', name: '穿衣建议', icon: 'fas fa-tshirt' },
                { id: 'car-wash', name: '洗车指数', icon: 'fas fa-car' },
                { id: 'sports', name: '运动指数', icon: 'fas fa-running' },
                { id: 'sun-times', name: '日出日落', icon: 'fas fa-clock' },
                { id: 'moon-phase', name: '月相', icon: 'fas fa-moon' }
            ],
            
            // 组件数据
            airQuality: { aqi: null, level: '' },
            uvIndex: { value: null, level: '' },
            precipitation: { probability: null, type: '' },
            clothing: { suggestion: '', description: '' },
            carWash: { index: null, suggestion: '' },
            sports: { index: null, suggestion: '' },
            sunTimes: { sunrise: '', sunset: '' },
            moonPhase: { icon: '', name: '' },
            
            // 设置
            showSettings: false,
            settings: {
                apiSource: 'openweather',
                apiKey: '',
                temperatureUnit: 'celsius',
                refreshInterval: 600000, // 10分钟
                enableNotifications: true
            },
            
            // 通知系统
            notification: {
                show: false,
                message: '',
                type: 'success' // success, error, warning
            },
            
            // 定时器
            refreshTimer: null,
            
            // API缓存
            cache: {
                weather: null,
                forecast: null,
                extended: null,
                lastUpdate: null,
                duration: 10 * 60 * 1000 // 10分钟缓存
            },
            
            // API配置
            apiConfigs: {
                openweather: {
                    baseUrl: 'https://api.openweathermap.org/data/2.5',
                    key: 'your_openweather_api_key'
                },
                amap: {
                    baseUrl: 'https://restapi.amap.com/v3',
                    key: 'your_amap_api_key'
                },
                baidu: {
                    baseUrl: 'https://api.map.baidu.com',
                    key: 'your_baidu_api_key'
                }
            }
        };
    },
    
    mounted() {
        this.initializeApp();
    },
    
    beforeUnmount() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }
    },
    
    methods: {
        /**
         * 初始化应用
         */
        async initializeApp() {
            this.loadSettings();
            this.loadDashboardLayout();
            
            // 尝试从缓存加载数据
            const hasCachedData = this.loadCacheFromStorage();
            if (hasCachedData) {
                this.loadFromCache();
            }
            
            await this.getCurrentLocation();
            await this.loadWeatherData();
            this.initializeChart();
            this.initializeDragAndDrop();
            this.setupAutoRefresh();
            
            // 添加离线/在线状态监听
            this.setupNetworkListeners();
        },
        
        /**
         * 获取当前位置
         */
        async getCurrentLocation() {
            try {
                if (navigator.geolocation) {
                    const position = await new Promise((resolve, reject) => {
                        navigator.geolocation.getCurrentPosition(resolve, reject);
                    });
                    
                    const { latitude, longitude } = position.coords;
                    this.currentLocation = await this.reverseGeocode(latitude, longitude);
                } else {
                    this.currentLocation = '北京市'; // 默认城市
                }
            } catch (error) {
                console.error('获取位置失败:', error);
                this.currentLocation = '北京市';
            }
        },
        
        /**
         * 反向地理编码
         */
        async reverseGeocode(lat, lon) {
            try {
                // 这里使用高德地图API进行反向地理编码
                const response = await fetch(
                    `https://restapi.amap.com/v3/geocode/regeo?location=${lon},${lat}&key=${this.apiConfigs.amap.key}&radius=1000&extensions=base`
                );
                const data = await response.json();
                
                if (data.status === '1' && data.regeocode) {
                    return data.regeocode.formatted_address;
                }
                return '未知位置';
            } catch (error) {
                console.error('反向地理编码失败:', error);
                return '未知位置';
            }
        },
        
        /**
         * 加载天气数据
         */
        async loadWeatherData(forceRefresh = false) {
            // 检查缓存
            if (!forceRefresh && this.isCacheValid()) {
                this.loadFromCache();
                return;
            }
            
            this.isLoading = true;
            
            try {
                await Promise.all([
                    this.loadCurrentWeather(),
                    this.loadForecastData(),
                    this.loadExtendedData()
                ]);
                
                // 更新缓存
                this.updateCache();
                
                this.updateTheme();
                this.updateChart();
                
                this.showNotification('天气数据更新成功', 'success');
            } catch (error) {
                console.error('加载天气数据失败:', error);
                
                // 如果有缓存数据，使用缓存
                if (this.cache.weather) {
                    this.loadFromCache();
                    this.showNotification('网络连接失败，显示缓存数据', 'warning');
                } else {
                    // API调用失败时使用演示数据
                    this.loadDemoData();
                    this.showNotification('API调用失败，正在显示演示数据。请在设置中配置有效的API密钥。', 'warning');
                }
            } finally {
                this.isLoading = false;
            }
        },
        
        /**
         * 加载当前天气
         */
        async loadCurrentWeather() {
            const apiSource = this.settings.apiSource;
            
            if (apiSource === 'openweather') {
                await this.loadOpenWeatherCurrent();
            } else {
                // 模拟数据
                this.currentWeather = {
                    temperature: Math.round(Math.random() * 30 + 5),
                    feelsLike: Math.round(Math.random() * 30 + 5),
                    description: ['晴朗', '多云', '小雨', '阴天'][Math.floor(Math.random() * 4)],
                    icon: 'sunny',
                    humidity: Math.round(Math.random() * 50 + 30),
                    windSpeed: Math.round(Math.random() * 20 + 5),
                    visibility: Math.round(Math.random() * 20 + 10),
                    pressure: Math.round(Math.random() * 100 + 1000)
                };
            }
        },
        
        /**
         * 使用OpenWeatherMap API加载当前天气
         */
        async loadOpenWeatherCurrent() {
            const apiKey = this.settings.apiKey || this.apiConfigs.openweather.key;
            const city = this.currentLocation || '北京';
            
            // 检查API密钥
            if (!apiKey || apiKey === 'your_openweather_api_key') {
                throw new Error('请配置有效的OpenWeatherMap API密钥');
            }
            
            try {
                const response = await fetch(
                    `${this.apiConfigs.openweather.baseUrl}/weather?q=${encodeURIComponent(city)}&appid=${apiKey}&units=metric&lang=zh_cn`
                );
                
                if (!response.ok) {
                    if (response.status === 401) {
                        throw new Error('API密钥无效，请检查设置');
                    }
                    throw new Error(`API请求失败: ${response.status}`);
                }
                
                const data = await response.json();
                
                this.currentWeather = {
                    temperature: Math.round(data.main.temp),
                    feelsLike: Math.round(data.main.feels_like),
                    description: data.weather[0].description,
                    icon: this.mapWeatherIcon(data.weather[0].icon),
                    humidity: data.main.humidity,
                    windSpeed: Math.round(data.wind.speed * 3.6), // m/s to km/h
                    visibility: Math.round(data.visibility / 1000),
                    pressure: data.main.pressure
                };
            } catch (error) {
                console.error('OpenWeatherMap API调用失败:', error);
                throw error;
            }
        },
        
        /**
         * 加载预报数据
         */
        async loadForecastData() {
            // 生成模拟的7天预报数据
            this.forecastData = [];
            const today = new Date();
            
            for (let i = 0; i < 7; i++) {
                const date = new Date(today);
                date.setDate(today.getDate() + i);
                
                this.forecastData.push({
                    date: date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }),
                    temperature: {
                        max: Math.round(Math.random() * 15 + 15),
                        min: Math.round(Math.random() * 10 + 5)
                    },
                    humidity: Math.round(Math.random() * 40 + 40),
                    windSpeed: Math.round(Math.random() * 15 + 5),
                    icon: ['sunny', 'cloudy', 'rainy', 'snowy'][Math.floor(Math.random() * 4)]
                });
            }
        },
        
        /**
         * 加载扩展数据（空气质量、紫外线等）
         */
        async loadExtendedData() {
            // 模拟扩展数据
            this.airQuality = {
                aqi: Math.round(Math.random() * 200 + 50),
                level: this.getAQILevel(Math.round(Math.random() * 200 + 50))
            };
            
            this.uvIndex = {
                value: Math.round(Math.random() * 10 + 1),
                level: this.getUVLevel(Math.round(Math.random() * 10 + 1))
            };
            
            this.precipitation = {
                probability: Math.round(Math.random() * 100),
                type: ['无降水', '小雨', '中雨', '大雨'][Math.floor(Math.random() * 4)]
            };
            
            this.clothing = {
                suggestion: this.getClothingSuggestion(this.currentWeather.temperature),
                description: '根据当前温度推荐'
            };
            
            this.carWash = {
                index: Math.round(Math.random() * 4 + 1),
                suggestion: this.getCarWashSuggestion(Math.round(Math.random() * 4 + 1))
            };
            
            this.sports = {
                index: Math.round(Math.random() * 4 + 1),
                suggestion: this.getSportsSuggestion(Math.round(Math.random() * 4 + 1))
            };
            
            // 计算日出日落时间
            const now = new Date();
            const sunrise = new Date(now);
            sunrise.setHours(6, 30, 0);
            const sunset = new Date(now);
            sunset.setHours(18, 45, 0);
            
            this.sunTimes = {
                sunrise: sunrise.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
                sunset: sunset.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
            };
            
            this.moonPhase = {
                icon: ['🌑', '🌒', '🌓', '🌔', '🌕', '🌖', '🌗', '🌘'][Math.floor(Math.random() * 8)],
                name: ['新月', '峨眉月', '上弦月', '盈凸月', '满月', '亏凸月', '下弦月', '残月'][Math.floor(Math.random() * 8)]
            };
        },
        
        /**
         * 搜索天气
         */
        async searchWeather() {
            if (!this.searchCity.trim()) return;
            
            this.currentLocation = this.searchCity.trim();
            this.searchCity = '';
            await this.loadWeatherData();
        },
        
        /**
         * 刷新天气数据
         */
        async refreshWeather() {
            await this.loadWeatherData(true); // 强制刷新
        },
        
        /**
         * 初始化图表
         */
        initializeChart() {
            const chartDom = document.getElementById('weatherChart');
            this.weatherChart = echarts.init(chartDom);
            this.updateChart();
            
            // 响应式调整
            window.addEventListener('resize', () => {
                this.weatherChart.resize();
            });
        },
        
        /**
         * 更新图表
         */
        updateChart() {
            if (!this.weatherChart || !this.forecastData.length) return;
            
            const dates = this.forecastData.map(item => item.date);
            let data, yAxisName, color;
            
            switch (this.chartType) {
                case 'temperature':
                    data = [
                        {
                            name: '最高温度',
                            type: 'line',
                            data: this.forecastData.map(item => item.temperature.max),
                            smooth: true,
                            lineStyle: { color: '#ff6b6b' },
                            itemStyle: { color: '#ff6b6b' }
                        },
                        {
                            name: '最低温度',
                            type: 'line',
                            data: this.forecastData.map(item => item.temperature.min),
                            smooth: true,
                            lineStyle: { color: '#4ecdc4' },
                            itemStyle: { color: '#4ecdc4' }
                        }
                    ];
                    yAxisName = '温度 (°C)';
                    break;
                    
                case 'humidity':
                    data = [{
                        name: '湿度',
                        type: 'line',
                        data: this.forecastData.map(item => item.humidity),
                        smooth: true,
                        lineStyle: { color: '#45b7d1' },
                        itemStyle: { color: '#45b7d1' },
                        areaStyle: { color: 'rgba(69, 183, 209, 0.2)' }
                    }];
                    yAxisName = '湿度 (%)';
                    break;
                    
                case 'wind':
                    data = [{
                        name: '风速',
                        type: 'bar',
                        data: this.forecastData.map(item => item.windSpeed),
                        itemStyle: { color: '#96ceb4' }
                    }];
                    yAxisName = '风速 (km/h)';
                    break;
            }
            
            const option = {
                tooltip: {
                    trigger: 'axis',
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    borderColor: 'rgba(255, 255, 255, 0.2)',
                    textStyle: { color: '#fff' }
                },
                legend: {
                    data: data.map(item => item.name),
                    textStyle: { color: '#fff' }
                },
                grid: {
                    left: '3%',
                    right: '4%',
                    bottom: '3%',
                    containLabel: true
                },
                xAxis: {
                    type: 'category',
                    data: dates,
                    axisLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.3)' } },
                    axisLabel: { color: '#fff' }
                },
                yAxis: {
                    type: 'value',
                    name: yAxisName,
                    nameTextStyle: { color: '#fff' },
                    axisLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.3)' } },
                    axisLabel: { color: '#fff' },
                    splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.1)' } }
                },
                series: data
            };
            
            this.weatherChart.setOption(option);
        },
        
        /**
         * 初始化拖拽功能
         */
        initializeDragAndDrop() {
            const grid = document.getElementById('dashboard-grid');
            
            Sortable.create(grid, {
                animation: 150,
                ghostClass: 'sortable-ghost',
                onEnd: (evt) => {
                    // 更新组件顺序
                    const oldIndex = evt.oldIndex;
                    const newIndex = evt.newIndex;
                    
                    const movedComponent = this.activeComponents.splice(oldIndex, 1)[0];
                    this.activeComponents.splice(newIndex, 0, movedComponent);
                    
                    this.saveDashboardLayout();
                }
            });
        },
        
        /**
         * 添加组件
         */
        addComponent(component) {
            if (!this.isComponentActive(component.id)) {
                this.activeComponents.push({ ...component });
                this.saveDashboardLayout();
                this.showNotification(`已添加 ${component.name} 组件`, 'success');
            }
        },
        
        /**
         * 移除组件
         */
        removeComponent(componentId) {
            const index = this.activeComponents.findIndex(c => c.id === componentId);
            if (index > -1) {
                const component = this.activeComponents[index];
                this.activeComponents.splice(index, 1);
                this.saveDashboardLayout();
                this.showNotification(`已移除 ${component.name} 组件`, 'success');
            }
        },
        
        /**
         * 检查组件是否已激活
         */
        isComponentActive(componentId) {
            return this.activeComponents.some(c => c.id === componentId);
        },
        
        /**
         * 更新主题
         */
        updateTheme() {
            const body = document.body;
            const icon = this.currentWeather.icon;
            
            // 移除所有主题类
            body.classList.remove('theme-sunny', 'theme-rainy', 'theme-snowy', 'theme-cloudy');
            
            // 根据天气图标设置主题
            if (icon.includes('sun') || icon === 'sunny') {
                body.classList.add('theme-sunny');
            } else if (icon.includes('rain') || icon === 'rainy') {
                body.classList.add('theme-rainy');
            } else if (icon.includes('snow') || icon === 'snowy') {
                body.classList.add('theme-snowy');
            } else {
                body.classList.add('theme-cloudy');
            }
        },
        
        /**
         * 设置自动刷新
         */
        setupAutoRefresh() {
            if (this.refreshTimer) {
                clearInterval(this.refreshTimer);
            }
            
            if (this.settings.refreshInterval > 0) {
                this.refreshTimer = setInterval(() => {
                    this.loadWeatherData();
                }, this.settings.refreshInterval);
            }
        },
        
        /**
         * 保存设置
         */
        saveSettings() {
            localStorage.setItem('weather-dashboard-settings', JSON.stringify(this.settings));
            this.setupAutoRefresh();
            this.showSettings = false;
            this.showNotification('设置已保存', 'success');
        },
        
        /**
         * 加载设置
         */
        loadSettings() {
            const saved = localStorage.getItem('weather-dashboard-settings');
            if (saved) {
                this.settings = { ...this.settings, ...JSON.parse(saved) };
            }
        },
        
        /**
         * 重置设置
         */
        resetSettings() {
            this.settings = {
                apiSource: 'openweather',
                apiKey: '',
                temperatureUnit: 'celsius',
                refreshInterval: 600000,
                enableNotifications: true
            };
            this.showNotification('设置已重置', 'warning');
        },
        
        /**
         * 保存仪表盘布局
         */
        saveDashboardLayout() {
            localStorage.setItem('weather-dashboard-layout', JSON.stringify(this.activeComponents));
        },
        
        /**
         * 加载仪表盘布局
         */
        loadDashboardLayout() {
            const saved = localStorage.getItem('weather-dashboard-layout');
            if (saved) {
                this.activeComponents = JSON.parse(saved);
            } else {
                // 默认组件
                this.activeComponents = [
                    { id: 'air-quality', name: '空气质量', icon: 'fas fa-leaf' },
                    { id: 'uv-index', name: '紫外线指数', icon: 'fas fa-sun' },
                    { id: 'sun-times', name: '日出日落', icon: 'fas fa-clock' }
                ];
            }
        },
        
        /**
         * 显示通知
         */
        showNotification(message, type = 'success') {
            this.notification = {
                show: true,
                message,
                type
            };
            
            setTimeout(() => {
                this.hideNotification();
            }, 3000);
        },
        
        /**
         * 隐藏通知
         */
        hideNotification() {
            this.notification.show = false;
        },
        
        // 工具方法
        
        /**
         * 获取天气图标
         */
        getWeatherIcon(iconCode) {
            const iconMap = {
                'sunny': 'fas fa-sun',
                'cloudy': 'fas fa-cloud',
                'rainy': 'fas fa-cloud-rain',
                'snowy': 'fas fa-snowflake',
                '01d': 'fas fa-sun',
                '01n': 'fas fa-moon',
                '02d': 'fas fa-cloud-sun',
                '02n': 'fas fa-cloud-moon',
                '03d': 'fas fa-cloud',
                '03n': 'fas fa-cloud',
                '04d': 'fas fa-cloud',
                '04n': 'fas fa-cloud',
                '09d': 'fas fa-cloud-rain',
                '09n': 'fas fa-cloud-rain',
                '10d': 'fas fa-cloud-sun-rain',
                '10n': 'fas fa-cloud-moon-rain',
                '11d': 'fas fa-bolt',
                '11n': 'fas fa-bolt',
                '13d': 'fas fa-snowflake',
                '13n': 'fas fa-snowflake',
                '50d': 'fas fa-smog',
                '50n': 'fas fa-smog'
            };
            
            return iconMap[iconCode] || 'fas fa-question';
        },
        
        /**
         * 映射天气图标
         */
        mapWeatherIcon(openWeatherIcon) {
            return openWeatherIcon;
        },
        
        /**
         * 获取空气质量等级
         */
        getAQILevel(aqi) {
            if (aqi <= 50) return '优';
            if (aqi <= 100) return '良';
            if (aqi <= 150) return '轻度污染';
            if (aqi <= 200) return '中度污染';
            if (aqi <= 300) return '重度污染';
            return '严重污染';
        },
        
        /**
         * 获取空气质量颜色
         */
        getAQIColor(aqi) {
            if (aqi <= 50) return 'bg-green-500';
            if (aqi <= 100) return 'bg-yellow-500';
            if (aqi <= 150) return 'bg-orange-500';
            if (aqi <= 200) return 'bg-red-500';
            if (aqi <= 300) return 'bg-purple-500';
            return 'bg-red-800';
        },
        
        /**
         * 获取紫外线等级
         */
        getUVLevel(uv) {
            if (uv <= 2) return '低';
            if (uv <= 5) return '中等';
            if (uv <= 7) return '高';
            if (uv <= 10) return '很高';
            return '极高';
        },
        
        /**
         * 获取穿衣建议
         */
        getClothingSuggestion(temp) {
            if (temp < 0) return '羽绒服';
            if (temp < 10) return '厚外套';
            if (temp < 20) return '薄外套';
            if (temp < 25) return '长袖';
            if (temp < 30) return '短袖';
            return '清凉装';
        },
        
        /**
         * 获取洗车建议
         */
        getCarWashSuggestion(index) {
            const suggestions = ['不适宜', '较不适宜', '适宜', '较适宜', '非常适宜'];
            return suggestions[index - 1] || '适宜';
        },
        
        /**
         * 获取运动建议
         */
        getSportsSuggestion(index) {
            const suggestions = ['不适宜', '较不适宜', '适宜', '较适宜', '非常适宜'];
            return suggestions[index - 1] || '适宜';
        },
        
        /**
         * 检查缓存是否有效
         */
        isCacheValid() {
            if (!this.cache.lastUpdate) return false;
            
            const now = Date.now();
            const timeDiff = now - this.cache.lastUpdate;
            
            return timeDiff < this.cache.duration;
        },
        
        /**
         * 从缓存加载数据
         */
        loadFromCache() {
            if (this.cache.weather) {
                this.currentWeather = { ...this.cache.weather };
            }
            
            if (this.cache.forecast) {
                this.forecastData = [...this.cache.forecast];
            }
            
            if (this.cache.extended) {
                const extended = this.cache.extended;
                this.airQuality = { ...extended.airQuality };
                this.uvIndex = { ...extended.uvIndex };
                this.precipitation = { ...extended.precipitation };
                this.clothing = { ...extended.clothing };
                this.carWash = { ...extended.carWash };
                this.sports = { ...extended.sports };
                this.sunTimes = { ...extended.sunTimes };
                this.moonPhase = { ...extended.moonPhase };
            }
            
            this.updateTheme();
            this.updateChart();
        },
        
        /**
         * 更新缓存
         */
        updateCache() {
            this.cache.weather = { ...this.currentWeather };
            this.cache.forecast = [...this.forecastData];
            this.cache.extended = {
                airQuality: { ...this.airQuality },
                uvIndex: { ...this.uvIndex },
                precipitation: { ...this.precipitation },
                clothing: { ...this.clothing },
                carWash: { ...this.carWash },
                sports: { ...this.sports },
                sunTimes: { ...this.sunTimes },
                moonPhase: { ...this.moonPhase }
            };
            this.cache.lastUpdate = Date.now();
            
            // 保存到本地存储
            this.saveCacheToStorage();
        },
        
        /**
         * 保存缓存到本地存储
         */
        saveCacheToStorage() {
            try {
                localStorage.setItem('weather-dashboard-cache', JSON.stringify(this.cache));
            } catch (error) {
                console.warn('保存缓存失败:', error);
            }
        },
        
        /**
         * 从本地存储加载缓存
         */
        loadCacheFromStorage() {
            try {
                const saved = localStorage.getItem('weather-dashboard-cache');
                if (saved) {
                    const cache = JSON.parse(saved);
                    
                    // 检查缓存是否过期
                    if (cache.lastUpdate && (Date.now() - cache.lastUpdate) < this.cache.duration) {
                        this.cache = { ...this.cache, ...cache };
                        return true;
                    }
                }
            } catch (error) {
                console.warn('加载缓存失败:', error);
            }
            return false;
        },
        
        /**
         * 清除缓存
         */
        clearCache() {
            this.cache = {
                weather: null,
                forecast: null,
                extended: null,
                lastUpdate: null,
                duration: 10 * 60 * 1000
            };
            
            try {
                localStorage.removeItem('weather-dashboard-cache');
            } catch (error) {
                console.warn('清除缓存失败:', error);
            }
        },
        
        /**
          * 获取缓存状态信息
          */
         getCacheStatus() {
             if (!this.cache.lastUpdate) {
                 return { status: 'empty', message: '无缓存数据' };
             }
             
             const now = Date.now();
             const timeDiff = now - this.cache.lastUpdate;
             const remainingTime = this.cache.duration - timeDiff;
             
             if (remainingTime > 0) {
                 const minutes = Math.floor(remainingTime / (60 * 1000));
                 const seconds = Math.floor((remainingTime % (60 * 1000)) / 1000);
                 return {
                     status: 'valid',
                     message: `缓存有效，剩余 ${minutes}:${seconds.toString().padStart(2, '0')}`
                 };
             } else {
                 return { status: 'expired', message: '缓存已过期' };
             }
         },
         
         /**
          * 设置网络状态监听
          */
         setupNetworkListeners() {
             // 监听在线/离线状态
             window.addEventListener('online', () => {
                 this.hideOfflineIndicator();
                 this.showNotification('网络连接已恢复', 'success');
                 // 网络恢复时自动刷新数据
                 this.loadWeatherData(true);
             });
             
             window.addEventListener('offline', () => {
                 this.showOfflineIndicator();
                 this.showNotification('网络连接已断开，将显示缓存数据', 'warning');
             });
             
             // 初始检查网络状态
             if (!navigator.onLine) {
                 this.showOfflineIndicator();
             }
         },
         
         /**
          * 显示离线指示器
          */
         showOfflineIndicator() {
             let indicator = document.querySelector('.offline-indicator');
             if (!indicator) {
                 indicator = document.createElement('div');
                 indicator.className = 'offline-indicator';
                 indicator.innerHTML = '<i class="fas fa-wifi mr-2"></i>网络连接已断开，正在显示缓存数据';
                 document.body.appendChild(indicator);
             }
             indicator.classList.add('show');
         },
         
         /**
          * 隐藏离线指示器
          */
         hideOfflineIndicator() {
             const indicator = document.querySelector('.offline-indicator');
             if (indicator) {
                 indicator.classList.remove('show');
             }
         },
         
         /**
           * 获取演示天气数据
           * @param {string} city - 城市名称
           * @returns {Object} 演示天气数据
           */
          getDemoWeatherData(city) {
              const demoData = {
                  current: {
                      temperature: Math.round(Math.random() * 20 + 10),
                      feelsLike: Math.round(Math.random() * 20 + 10),
                      description: ['晴朗', '多云', '小雨', '阴天'][Math.floor(Math.random() * 4)],
                      icon: 'sunny',
                      humidity: Math.round(Math.random() * 40 + 40),
                      windSpeed: Math.round(Math.random() * 15 + 5),
                      visibility: Math.round(Math.random() * 20 + 10),
                      pressure: Math.round(Math.random() * 50 + 1000),
                      city: city || '演示城市'
                  },
                  forecast: [],
                  extended: {
                      airQuality: {
                          aqi: Math.round(Math.random() * 150 + 50),
                          level: '良好'
                      },
                      uvIndex: {
                          value: Math.round(Math.random() * 8 + 1),
                          level: '中等'
                      },
                      precipitation: {
                          probability: Math.round(Math.random() * 80 + 10),
                          type: '无降水'
                      }
                  }
              };
              
              // 生成7天预报数据
              const today = new Date();
              for (let i = 0; i < 7; i++) {
                  const date = new Date(today);
                  date.setDate(today.getDate() + i);
                  
                  demoData.forecast.push({
                      date: date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }),
                      temperature: {
                          max: Math.round(Math.random() * 15 + 15),
                          min: Math.round(Math.random() * 10 + 5)
                      },
                      humidity: Math.round(Math.random() * 40 + 40),
                      windSpeed: Math.round(Math.random() * 15 + 5),
                      description: ['晴', '多云', '雨', '阴'][Math.floor(Math.random() * 4)]
                  });
              }
              
              return demoData;
          },
          
          /**
           * 加载演示数据到界面
           */
          loadDemoData() {
             // 生成演示的当前天气数据
             this.currentWeather = {
                 temperature: Math.round(Math.random() * 20 + 10),
                 feelsLike: Math.round(Math.random() * 20 + 10),
                 description: ['晴朗', '多云', '小雨', '阴天'][Math.floor(Math.random() * 4)],
                 icon: 'sunny',
                 humidity: Math.round(Math.random() * 40 + 40),
                 windSpeed: Math.round(Math.random() * 15 + 5),
                 visibility: Math.round(Math.random() * 20 + 10),
                 pressure: Math.round(Math.random() * 50 + 1000)
             };
             
             // 生成演示的预报数据
             this.forecastData = [];
             const today = new Date();
             
             for (let i = 0; i < 7; i++) {
                 const date = new Date(today);
                 date.setDate(today.getDate() + i);
                 
                 this.forecastData.push({
                     date: date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }),
                     temperature: {
                         max: Math.round(Math.random() * 15 + 15),
                         min: Math.round(Math.random() * 10 + 5)
                     },
                     humidity: Math.round(Math.random() * 40 + 40),
                     windSpeed: Math.round(Math.random() * 15 + 5),
                     icon: ['sunny', 'cloudy', 'rainy', 'snowy'][Math.floor(Math.random() * 4)]
                 });
             }
             
             // 生成演示的扩展数据
             this.airQuality = {
                 aqi: Math.round(Math.random() * 150 + 50),
                 level: this.getAQILevel(Math.round(Math.random() * 150 + 50))
             };
             
             this.uvIndex = {
                 value: Math.round(Math.random() * 8 + 1),
                 level: this.getUVLevel(Math.round(Math.random() * 8 + 1))
             };
             
             this.precipitation = {
                 probability: Math.round(Math.random() * 80 + 10),
                 type: ['无降水', '小雨', '中雨'][Math.floor(Math.random() * 3)]
             };
             
             this.clothing = {
                 suggestion: this.getClothingSuggestion(this.currentWeather.temperature),
                 description: '根据当前温度推荐（演示数据）'
             };
             
             this.carWash = {
                 index: Math.round(Math.random() * 3 + 2),
                 suggestion: this.getCarWashSuggestion(Math.round(Math.random() * 3 + 2))
             };
             
             this.sports = {
                 index: Math.round(Math.random() * 3 + 2),
                 suggestion: this.getSportsSuggestion(Math.round(Math.random() * 3 + 2))
             };
             
             // 计算日出日落时间
             const now = new Date();
             const sunrise = new Date(now);
             sunrise.setHours(6, 30, 0);
             const sunset = new Date(now);
             sunset.setHours(18, 45, 0);
             
             this.sunTimes = {
                 sunrise: sunrise.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
                 sunset: sunset.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
             };
             
             this.moonPhase = {
                 icon: ['🌑', '🌒', '🌓', '🌔', '🌕', '🌖', '🌗', '🌘'][Math.floor(Math.random() * 8)],
                 name: ['新月', '峨眉月', '上弦月', '盈凸月', '满月', '亏凸月', '下弦月', '残月'][Math.floor(Math.random() * 8)]
             };
             
             // 更新缓存
             this.updateCache();
             
             // 更新界面
              this.updateTheme();
              this.updateCharts();
          },
          
          /**
           * 获取AQI等级描述
           * @param {number} aqi - AQI数值
           * @returns {string} 等级描述
           */
          getAQILevel(aqi) {
              if (aqi <= 50) return '优';
              if (aqi <= 100) return '良';
              if (aqi <= 150) return '轻度污染';
              if (aqi <= 200) return '中度污染';
              if (aqi <= 300) return '重度污染';
              return '严重污染';
          },
          
          /**
           * 获取UV等级描述
           * @param {number} uv - UV指数
           * @returns {string} 等级描述
           */
          getUVLevel(uv) {
              if (uv <= 2) return '低';
              if (uv <= 5) return '中等';
              if (uv <= 7) return '高';
              if (uv <= 10) return '很高';
              return '极高';
          },
          
          /**
           * 获取穿衣建议
           * @param {number} temp - 温度
           * @returns {string} 穿衣建议
           */
          getClothingSuggestion(temp) {
              if (temp < 0) return '羽绒服、厚棉衣';
              if (temp < 10) return '棉衣、冬大衣';
              if (temp < 15) return '风衣、毛衣';
              if (temp < 20) return '薄外套、长袖';
              if (temp < 25) return '长袖、薄衫';
              if (temp < 30) return '短袖、薄裤';
              return '短袖、短裤';
          },
          
          /**
           * 获取洗车建议
           * @param {number} index - 洗车指数
           * @returns {string} 洗车建议
           */
          getCarWashSuggestion(index) {
              const suggestions = {
                  1: '不适宜洗车',
                  2: '较不适宜洗车', 
                  3: '适宜洗车',
                  4: '很适宜洗车',
                  5: '非常适宜洗车'
              };
              return suggestions[index] || '适宜洗车';
          },
          
          /**
           * 获取运动建议
           * @param {number} index - 运动指数
           * @returns {string} 运动建议
           */
          getSportsSuggestion(index) {
              const suggestions = {
                  1: '不适宜运动',
                  2: '较不适宜运动',
                  3: '适宜运动', 
                  4: '很适宜运动',
                  5: '非常适宜运动'
              };
              return suggestions[index] || '适宜运动';
          }
    }
}).mount('#app');