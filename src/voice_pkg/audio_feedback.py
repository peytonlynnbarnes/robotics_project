import pyttsx3

def speak(text):
    print(f"[ROBOT]: {text}")
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print(f"Audio error: {e}")
