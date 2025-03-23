import time
import json
import logging
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_zhihu_page(keyword="编程竞赛"):
    """获取知乎搜索页面的结构以便调试"""
    logger.info(f"开始调试知乎页面结构，关键词: {keyword}")
    
    # 确保输出目录存在
    os.makedirs("debug", exist_ok=True)
    
    try:
        # 读取cookies
        cookies_dict = {}
        try:
            with open("config/api_keys.json", 'r', encoding='utf-8') as f:
                api_keys = json.load(f)
                zhihu_cookies = api_keys.get("zhihu", {}).get("cookies", [])
                for cookie in zhihu_cookies:
                    if isinstance(cookie, dict) and 'name' in cookie and 'value' in cookie:
                        cookies_dict[cookie['name']] = cookie['value']
        except Exception as e:
            logger.error(f"读取cookies失败: {str(e)}")
        
        # 初始化WebDriver
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # 修改webdriver属性
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        })
        
        # 访问知乎首页并设置cookies
        driver.get("https://www.zhihu.com/")
        for cookie_name, cookie_value in cookies_dict.items():
            driver.add_cookie({
                'name': cookie_name,
                'value': cookie_value,
                'domain': '.zhihu.com',
            })
        
        # 访问搜索页
        logger.info("访问知乎搜索页...")
        search_url = f"https://www.zhihu.com/search?q={keyword}&type=content"
        driver.get(search_url)
        logger.info("等待页面加载...")
        time.sleep(10)  # 给页面充分时间加载
        
        # 获取页面源码
        page_source = driver.page_source
        
        # 保存原始HTML
        with open("debug/zhihu_page.html", 'w', encoding='utf-8') as f:
            f.write(page_source)
        logger.info("已保存原始HTML到 debug/zhihu_page.html")
        
        # 使用BeautifulSoup解析页面
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # 查找所有可能的内容元素
        selectors = [
            ".Card", ".SearchResult-Card", ".List-item", 
            "div.SearchMain div.Card", ".AnswerItem", 
            ".ContentItem", "div[itemprop='answer']"
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            logger.info(f"选择器 '{selector}' 找到 {len(elements)} 个元素")
            
            # 保存前3个元素的代码
            if elements:
                for i, elem in enumerate(elements[:3]):
                    with open(f"debug/element_{selector.replace('.', '_').replace('[', '_').replace(']', '_').replace('=', '_')}_{i}.html", 'w', encoding='utf-8') as f:
                        f.write(str(elem))
                    logger.info(f"已保存元素到 debug/element_{selector.replace('.', '_')}_{i}.html")
        
        # 查找页面中的所有heading元素
        headings = soup.find_all(["h1", "h2", "h3"])
        logger.info(f"找到 {len(headings)} 个标题元素")
        with open("debug/headings.txt", 'w', encoding='utf-8') as f:
            for h in headings:
                f.write(f"{h.name}: {h.get_text(strip=True)}\n")
                f.write(f"HTML: {str(h)}\n\n")
        
        # 查找所有文本块
        texts = []
        for tag in soup.find_all(["p", "div", "span"]):
            text = tag.get_text(strip=True)
            if len(text) > 50:  # 只保留较长的文本
                texts.append((tag.name, text))
        
        logger.info(f"找到 {len(texts)} 个长文本块")
        with open("debug/text_blocks.txt", 'w', encoding='utf-8') as f:
            for tag_name, text in texts:
                f.write(f"Tag: {tag_name}\n")
                f.write(f"Text: {text[:100]}...\n\n")
        
        # 获取页面标题
        title = soup.title.string if soup.title else "无标题"
        logger.info(f"页面标题: {title}")
        
        # 执行JavaScript获取页面状态
        page_ready_state = driver.execute_script("return document.readyState")
        logger.info(f"页面加载状态: {page_ready_state}")
        
        # 检查是否有验证码或登录墙
        has_captcha = "验证码" in page_source or "验证" in page_source
        has_login_wall = "登录" in page_source and "继续浏览" in page_source
        logger.info(f"检测到验证码: {has_captcha}")
        logger.info(f"检测到登录墙: {has_login_wall}")
        
        # 查找所有链接
        all_links = soup.find_all("a", href=True)
        question_links = [link for link in all_links if "/question/" in link.get("href", "")]
        answer_links = [link for link in all_links if "/answer/" in link.get("href", "")]
        
        logger.info(f"找到 {len(question_links)} 个问题链接")
        logger.info(f"找到 {len(answer_links)} 个回答链接")
        
        with open("debug/links.txt", 'w', encoding='utf-8') as f:
            f.write("问题链接:\n")
            for link in question_links[:10]:  # 只保存前10个
                f.write(f"{link.get('href')}: {link.get_text(strip=True)[:50]}\n")
            
            f.write("\n回答链接:\n")
            for link in answer_links[:10]:  # 只保存前10个
                f.write(f"{link.get('href')}: {link.get_text(strip=True)[:50]}\n")
                
        return {
            "success": True,
            "message": "已保存调试信息",
            "has_captcha": has_captcha,
            "has_login_wall": has_login_wall,
            "title": title
        }
    
    except Exception as e:
        logger.error(f"调试过程中出错: {str(e)}")
        return {"success": False, "error": str(e)}
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    result = debug_zhihu_page()
    print(json.dumps(result, ensure_ascii=False, indent=2))
