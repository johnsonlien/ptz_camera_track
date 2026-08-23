from ultralytics import YOLO

model = YOLO("yolo11n_fish.pt")
for class_id, class_name in model.names.items():
    print(f"{class_id}: {class_name}")
#results = model(source=0, show=True, stream=True)

#for r in results:
#    pass



