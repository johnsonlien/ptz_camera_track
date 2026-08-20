
class TargetSelector:

    def __init__(self, strategy="manual"):
        """
        strategy = manual, highest_confidence
        """

        self.strategy = strategy
        self.locked_id = None

    def select(self, results):
        boxes = results.boxes

        if boxes is None or boxes.id is None:
            print("No objects detected...")
            return None

        if self.locked_id is not None and self.locked_id in boxes.id.tolist():
            print(f"Locked id: {locked_id}")
            return self.locked_id

        if self.strategy == "highest_confidence":
            best_idx = int(boxes.conf.argmax())
        else:
            best_idx = 0

        self.locked_id = int(boxes.id[best_idx].item())
        
        return self.locked_id

    def release(self):
        self.locked_id = None
