from streamlit_webrtc import VideoProcessorBase, RTCConfiguration,WebRtcMode,webrtc_streamer
from utils import *
import cv2
import streamlit as st
import mediapipe as mp
import av
RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

def calculate_angle(a,b,c):
    a = np.array(a) # First
    b = np.array(b) # Mid
    c = np.array(c) # End
    
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians*180.0/np.pi)
    
    if angle >180.0:
        angle = 360-angle
        
    return angle 


cap = cv2.VideoCapture(0)

# Curl counter variables
counter = 0 
stage = None

def main():
    st.header("Live stream processing")

    sign_language_det = "Left Hand"
    app_mode = st.sidebar.selectbox( "Choose the app mode",
        [
            sign_language_det
        ],
    )

    st.subheader(app_mode)

    if app_mode == sign_language_det:
        Left_hand()
 

def Left_hand():

    class OpenCVVideoProcessor(VideoProcessorBase):
        def recv(self, frame: av.VideoFrame) -> av.VideoFrame:

            with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
                while cap.isOpened():
                    ret, frame = cap.read()
                    
                    # Recolor image to RGB
                    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    image.flags.writeable = False
                
                    # Make detection
                    results = pose.process(image)
                
                    # Recolor back to BGR
                    image.flags.writeable = True
                    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                    
                    # Extract landmarks
                    try:
                        landmarks = results.pose_landmarks.landmark
                        
                        # Get coordinates
                        shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                        elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
                        wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
                        
                        # Calculate angle
                        angle = calculate_angle(shoulder, elbow, wrist)
                        
                        # Visualize angle
                        cv2.putText(image, str(angle), 
                                    tuple(np.multiply(elbow, [640, 480]).astype(int)), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA
                                            )
                        
                        # Curl counter logic
                        if angle > 160:
                            stage = "down"
                        if angle < 40 and stage =='down':
                            stage="up"
                            counter +=1
                            print(counter)
                                
                    except:
                        pass
                    
                    # Render curl counter
                    # Setup status box
                    cv2.rectangle(image, (0,0), (245,85), (245,117,16), -1)
                    
                    # Rep data
                    cv2.putText(image, 'REPS', (15,12), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)
                    cv2.putText(image, str(counter), 
                                (10,80), 
                                cv2.FONT_HERSHEY_SIMPLEX, 2, (255,255,255), 2, cv2.LINE_AA)
                    
                    # Stage data
                    cv2.putText(image, 'STAGE', (120,12), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)
                    cv2.putText(image, stage, 
                                (90,80), 
                                cv2.FONT_HERSHEY_SIMPLEX, 2, (255,255,255), 2, cv2.LINE_AA)
                    
                    
                    # Render detections
                    mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                            mp_drawing.DrawingSpec(color=(0,0,255), thickness=2, circle_radius=2), 
                                            mp_drawing.DrawingSpec(color=(255,255,0), thickness=2, circle_radius=2) 
                                            )               

                            
                     
                return av.VideoFrame.from_ndarray(image,format="bgr24")

    webrtc_ctx = webrtc_streamer(
        key="opencv-filter",
        mode=WebRtcMode.SENDRECV,
        rtc_configuration=RTC_CONFIGURATION,
        video_processor_factory=OpenCVVideoProcessor,
        async_processing=True,
    )


if __name__ == "__main__":
    main()