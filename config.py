# DeepSeek API 配置 
DEEPSEEK_API_KEY = 'sk-YvCOEo1Hoe1y3GGxZhg2asjHZ0b1OgSqGScpQ5LHEjolGQUQ'
# 硅基流动API注册地址，免费15元额度 https://cloud.siliconflow.cn/
DEEPSEEK_BASE_URL = 'https://vg.v1api.cc/v1'
# 硅基流动API的模型
MODEL = 'gpt-4o'

# 如果要使用官方的API
# DEEPSEEK_BASE_URL = 'https://api.deepseek.com'
# 官方API的V3模型
# MODEL = 'deepseek-chat'

# 回复最大token
MAX_TOKEN = 2000
# DeepSeek温度
TEMPERATURE = 1.1

LOCAL_MODEL_URL = 'http://localhost:1234/v1/chat/completions'
LOCAL_MODEL_NAME = 'qwen2.5-coder-3b-instruct'
MODEL_TYPE = 'LOCAL' # 除了LOCAL以外都是采用API

# 快捷键重新设置后需要托盘退出重进
REPLACE_HOTKEY = 'ctrl+.'
APPEND_HOTKEY = 'ctrl+/'

# TAVILY_API_KEY = ''
# ENABLE_TOOLS = True