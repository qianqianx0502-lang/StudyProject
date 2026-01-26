import cv2
import requests
import time
import threading
import numpy as np

# ESP8266的IP地址
ESP8266_IP = "192.168.1.12"
LED_ON_URL = f"http://{ESP8266_IP}/led/on"
LED_OFF_URL = f"http://{ESP8266_IP}/led/off"

class FaceDetectorHTTP:
    def __init__(self):
        self.face_detected = False
        self.last_detection_time = 0
        self.detection_cooldown = 2
        
        # 加载人脸检测器
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        try:
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            if self.face_cascade.empty():
                raise ValueError("无法加载人脸检测器")
        except:
            print("无法加载默认人脸检测器，尝试其他方法...")
            # 尝试其他路径
            import os
    
    def send_http_command(self, state):
        """发送HTTP命令到ESP8266"""
        def send_request():
            try:
                url = LED_ON_URL if state == "on" else LED_OFF_URL
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    print(f"HTTP命令发送成功: LED {state}")
                else:
                    print(f"HTTP请求失败: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"无法连接到ESP8266: {e}")
        
        # 在新线程中发送请求，避免阻塞主线程
        thread = threading.Thread(target=send_request)
        thread.daemon = True
        thread.start()
    
    def run(self):
        # 尝试打开摄像头
        cap = cv2.VideoCapture(0)
        # 设置摄像头分辨率
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        if not cap.isOpened():
            print("无法打开摄像头，尝试其他索引...")
            for i in range(1, 5):
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    print(f"使用摄像头索引 {i}")
                    break
            else:
                print("错误：没有可用的摄像头")
                return
        
        print("=" * 50)
        print("人脸识别HTTP版本")
        print(f"ESP8266 IP: {ESP8266_IP}")
        print("按 'q' 键退出程序")
        print("=" * 50)
        
        frame_count = 0
        detection_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("无法读取视频帧")
                time.sleep(0.5)
                continue
            
            frame_count += 1
            # 每2帧处理一次，提高性能
            if frame_count % 2 != 0:
                continue
            
            # 转换为灰度图
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # 均衡化，提高检测效果
            gray_eq = cv2.equalizeHist(gray)
            
            # 检测人脸
            faces = self.face_cascade.detectMultiScale(
                gray_eq,
                scaleFactor=1.05,  # 稍微降低以提高准确性
                minNeighbors=5,    # 增加以减少误报
                minSize=(50, 50),  # 增加最小尺寸
                maxSize=(300, 300) # 增加最大尺寸
            )
            print(f'faces: {faces}')
            
            current_time = time.time()
            
            # 如果检测到人脸
            if len(faces) > 0:
                valid_faces = []
                for (x, y, w, h) in faces:
                    # 提取人脸区域
                    face_region = gray[y:y+h, x:x+w]
                    # 计算平均亮度
                    brightness = np.mean(face_region)
                    
                    # 设置亮度阈值，例如：30 < brightness < 220
                    if 30 < brightness < 220:
                        valid_faces.append((x, y, w, h))
                
                # 如果经过亮度过滤后还有有效人脸，才进行处理
                if len(valid_faces) > 0:
                    # 绘制有效人脸框
                    for (x, y, w, h) in valid_faces:
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        cv2.putText(frame, 'Face', (x, y-10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    
                    # 在左上角显示状态
                    cv2.putText(frame, f'Faces: {len(valid_faces)}', (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    if not self.face_detected and (current_time - self.last_detection_time > self.detection_cooldown):
                        print(f"[{time.strftime('%H:%M:%S')}] 检测到 {len(valid_faces)} 个人脸")
                        self.send_http_command("on")
                        self.face_detected = True
                        self.last_detection_time = current_time
                else:
                    # 如果没有有效人脸，则按无人脸处理
                    if self.face_detected and (current_time - self.last_detection_time > self.detection_cooldown):
                        print(f"[{time.strftime('%H:%M:%S')}] 人脸消失")
                        self.send_http_command("off")
                        self.face_detected = False
            
            # 如果人脸消失
            else:
                if self.face_detected and (current_time - self.last_detection_time > self.detection_cooldown):
                    print(f"[{time.strftime('%H:%M:%S')}] 人脸消失")
                    self.send_http_command("off")
                    self.face_detected = False
            
            # 显示帧率
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps > 0:
                cv2.putText(frame, f'FPS: {fps:.1f}', (10, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # 显示窗口
            cv2.imshow('Face Detection - Press Q to quit', frame)
            
            # 按'q'退出
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        # 清理资源
        cap.release()
        cv2.destroyAllWindows()
        self.send_http_command("off")
        print("程序已退出")

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
    print("人脸识别系统初始化...")
    
    # 测试连接
    if test_esp8266_connection():
        detector = FaceDetectorHTTP()
        detector.run()
    else:
        print("连接测试失败，请检查配置")