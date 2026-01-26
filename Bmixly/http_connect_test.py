import requests

# ESP8266的IP地址
ESP8266_IP = "192.168.1.12:8000"
TEST_URL = f"http://{ESP8266_IP}/text/plain"

def test_esp8266_connection():
    """测试ESP8266连接"""
    print("测试ESP8266连接...")
    try:
        response = requests.get(f"http://{ESP8266_IP}/", timeout=3)
        if response.status_code == 200:
            print(f"✓ ESP8266连接成功 (IP: {ESP8266_IP})")
            return True
    except:
        print(f"✗ 无法连接到ESP8266 (IP: {ESP8266_IP})")
        print("请确保:")
        print("1. ESP8266已连接到同一WiFi网络")
        print("2. IP地址正确")
        print("3. ESP8266已上传Web服务器程序")
        return False

if __name__ == "__main__":    
    # 测试连接
    if test_esp8266_connection():
        print("连接测试成功")
    else:
        print("连接测试失败，请检查配置")