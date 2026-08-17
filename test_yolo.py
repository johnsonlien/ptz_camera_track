from ultralytics import YOLO

model = YOLO("yolo11n.pt")

results = model(source=0, show=True, stream=True)

for r in results:
    pass
