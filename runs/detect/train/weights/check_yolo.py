from ultralytics import YOLO 

model = YOLO("./best.pt")

results = model("./decent_fish.JPG")

results[0].save(filename="output.jpg")
