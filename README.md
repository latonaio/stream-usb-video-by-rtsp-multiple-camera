# stream-usb-video-by-rtsp-multiple-camera
stream-usb-video-by-rtsp-multiple-cameraは、主にエッジコンピューティング環境において、接続された複数のUSBカメラから画像データを取得し、RTSP方式で他マイクロサービスに画像データを配信するマイクロサービスです。  
配信は、RabbitMQにより行われます。  

# 動作環境   
stream-usb-video-by-rtsp-multiple-cameraは、aion-coreのプラットフォーム上での動作を前提としています。  
使用する際は、事前に下記の通りAIONの動作環境を用意してください。  
 
* Linux OS  
* ARM/AMD/Intel     
* Kubernetes  
* AIONのリソース    

# カメラ設定
下記のpathに配置してある設定ファイルを読み込んで、auto_focusなどの設定を行います。

`/var/lib/aion/Data/stream-usb-video-by-rtsp_{MS_NUMBER}/config.json`

現状では各設定はデフォルトとして以下の状態に設定されています。（変更不可）
```
auto_focus：True
focus_absolute: 50
```

# I/O
RabbitMQにより、下記のデータを入出力します。
### input

* device_list: [check-multiple-camera-multiple-device-connection-kube](https://github.com/latonaio/check-multiple-camera-multiple-device-connection-kube)で生成された、接続されたデバイスのリスト
* auto_focus: オートフォーカスの設定

### output
- width: 解像度横幅 
- height: 解像度縦幅 
- framerate: 秒間フレームレート
- addr:rtspで通信するためのuri。`rtsp://{SERVICE_NAME}-{MS_NUMBER}-srv:{ポート番号}`の形式になります。

※ ポート番号は、環境変数で指定したデフォルトの番号に、全登録デバイスの中のそのデバイスの登録順を加えたものが割り振られます。

※ docker環境では一律`localhost:{port}`に指定されます。


## 環境変数
- WIDTH(解像度横幅,default: 864)
- HEIGHT(解像度縦幅,default: 480)
- FPSI(フレームレート,default: 10)
- PORT(TSP通信ポート,default: 8554)
- URI(RTSP通信アドレス,default:"/usb")
- MS_NUMBER(aion-core全体の変数. 値はproject.yamlを参照してください)

## デプロイ on AION
AION上でデプロイする場合、services.yamlに次の設定を追加してください。
```
  stream-usb-video-by-rtsp-multiple-camera:
    scale: 1
    startup: yes
    always: yes
    network: NodePort
    privileged: yes
    ports:
      - name: usb
        protocol: TCP
        port: 8555
        nodePort: 30055
    env:
      SUFFIX: 1
      RABBITMQ_URL: amqp://guest:guest@rabbitmq:5672/famanager
      QUEUE_ORIGIN: stream-usb-video-by-rtsp-multiple-camera-queue
      QUEUE_TO: template-matching-by-opencv-for-rtsp-queue
```