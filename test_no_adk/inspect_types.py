from google.genai import types
import inspect

def print_fields(cls):
    print(f"--- {cls.__name__} ---")
    if hasattr(cls, "model_fields"):
        for name, field in cls.model_fields.items():
            print(f"{name}: {field.annotation}")
    else:
        print(dir(cls))

print("Searching for Activity Detection...")
if hasattr(types, "AutomaticActivityDetection"):
    print("Found AutomaticActivityDetection")
    # print_fields(types.AutomaticActivityDetection)
else:
    print("AutomaticActivityDetection NOT found in types root.")

print("\n--- LiveConnectConfig ---")
print_fields(types.LiveConnectConfig)

print("\n--- GenerationConfig ---")
print_fields(types.GenerationConfig)

print("\n--- SpeechConfig ---")
print_fields(types.SpeechConfig)

print("\n--- VoiceConfig ---")
print_fields(types.VoiceConfig)
