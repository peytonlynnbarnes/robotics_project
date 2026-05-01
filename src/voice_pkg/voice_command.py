import speech_recognition as sr

def listen_for_command():
  recognizer = sr.Recognizer()
  with sr.Microphone() as source:
    recognizer.adjust_for_ambient_noise(source, duration=1)
    try:
      audio = recognizer.listen(source, timeout=5)
      command = recognizer.recognize_google(audio)
      print(f"[USER RECEIVED]: {command}")
      return command.lower()
    except Exception:
      return None
