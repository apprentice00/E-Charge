### 环境
* node.js
* vue3
* npm install axios
* python
* flask flask-cors

都安装最新版本即可
后端基于Python Flask 实现

### 启动
前端
```shell
cd Frontend
npm install     # 第一次启动时执行，后续不需要
npm run dev
```
后端，登录接口(app.py 简单实现)
```shell
cd Backend
python app.py
```

### 实现
#### 登录
1. 输入账号和密码，前端将数据发送到后端
2. 后端通过验证，如果验证成功，返回用户类型
3. 前端根据用户类型跳转
数据：
* frontend send {username, password}
* backend return {type}

#### 注册
只能注册用户