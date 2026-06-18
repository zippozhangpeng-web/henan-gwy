# ==========================================
# Dockerfile — 好风公考情报站
# ==========================================
FROM python:3.11-slim

LABEL maintainer="好风公考情报站"
LABEL description="河南公考岗位情报站 - Flask Web应用"

WORKDIR /app

# 时区设置
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 生成演示数据
RUN python seed_data.py

# 暴露端口
EXPOSE 5050
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5050/health')" || exit 1

# 启动
CMD ["python", "app.py"]
