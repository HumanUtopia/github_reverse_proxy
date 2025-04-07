import requests
import logging
import gzip
from flask import Flask, request, Response, render_template_string
import os
import sys
from urllib.parse import urljoin

# 配置详细的日志记录
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# 清除任何可能干扰的代理环境变量
for env_var in ['http_proxy', 'https_proxy', 'no_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'NO_PROXY']:
    if env_var in os.environ:
        del os.environ[env_var]

app = Flask(__name__)


@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS', 'PATCH'])
def proxy(path):
    target_url = f"https://github.com/{path}"
    app.logger.debug(f"准备代理请求到: {target_url}")
    app.logger.debug(f"请求方法: {request.method}")

    # 获取原始头信息但过滤掉可能导致问题的头
    headers = {key: value for key, value in request.headers.items()
               if key.lower() not in ['host', 'connection', 'content-length', 'content-encoding', 'transfer-encoding']}

    # 保留原始的 User-Agent，可能对某些网站很重要
    if 'User-Agent' in request.headers:
        headers['User-Agent'] = request.headers['User-Agent']
    else:
        headers[
            'User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

    # 添加 X-Forwarded 头信息
    headers['X-Forwarded-For'] = request.remote_addr
    headers['X-Forwarded-Proto'] = request.scheme

    app.logger.debug(f"修改后的请求头: {headers}")

    try:
        # 使用 session 以更好地控制连接
        session = requests.Session()
        session.trust_env = False  # 不使用环境变量中的代理设置

        # 使用流式传输以更好地处理大型响应
        response = session.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            timeout=30,
            verify=True,
            stream=True  # 使用流式传输
        )

        app.logger.debug(f"GitHub 响应状态码: {response.status_code}")
        app.logger.debug(f"GitHub 响应头: {dict(response.headers)}")

        # 准备响应头，但排除一些会导致问题的头
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        response_headers = [(name, value) for name, value in response.headers.items()
                            if name.lower() not in excluded_headers]

        # 获取响应内容
        content = response.raw.read()

        # 处理压缩内容
        if response.headers.get('Content-Encoding') == 'gzip':
            try:
                content = gzip.decompress(content)
                # 既然我们已经解压了内容，就移除这个头信息
                response_headers = [(name, value) for name, value in response_headers
                                    if name.lower() != 'content-encoding']
            except Exception as e:
                app.logger.error(f"解压缩错误: {str(e)}")
                # 如果解压失败，继续使用原始内容

        # 创建响应
        flask_response = Response(content, response.status_code, response_headers)

        # 处理重定向
        if 300 <= response.status_code < 400:
            location = response.headers.get('Location')
            if location:
                # 如果是绝对 URL，保持不变
                if location.startswith(('http://', 'https://')):
                    flask_response.headers['Location'] = location
                # 如果是相对 URL，确保它指向我们的代理
                else:
                    base_url = request.url_root.rstrip('/')
                    flask_response.headers['Location'] = f"{base_url}/{location.lstrip('/')}"

        return flask_response

    except requests.exceptions.RequestException as e:
        app.logger.error(f"代理错误: {str(e)}", exc_info=True)
        return error_page(f"代理错误: {str(e)}", 502)
    except Exception as e:
        app.logger.error(f"未预期的错误: {str(e)}", exc_info=True)
        return error_page(f"服务器错误: {str(e)}", 500)


@app.route('/', methods=['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS', 'PATCH'])
def root():
    return proxy("")


# 添加一个健康检查端点
@app.route('/health', methods=['GET'])
def health_check():
    return Response("OK", status=200)


# 错误页面生成器
def error_page(message, status_code):
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Error {status_code}</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; }}
            .error-container {{ max-width: 800px; margin: 0 auto; background-color: #f8f9fa; padding: 20px; border-radius: 5px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #e74c3c; }}
            pre {{ background-color: #f1f1f1; padding: 10px; border-radius: 5px; overflow-x: auto; }}
        </style>
    </head>
    <body>
        <div class="error-container">
            <h1>Error {status_code}</h1>
            <p>{message}</p>
            <p>若需要帮助，请联系系统管理员。</p>
        </div>
    </body>
    </html>
    """
    return Response(html, status=status_code, content_type='text/html')


# 添加静态资源处理
@app.route('/assets/<path:asset_path>')
def proxy_assets(asset_path):
    return proxy(f"assets/{asset_path}")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True, threaded=True)