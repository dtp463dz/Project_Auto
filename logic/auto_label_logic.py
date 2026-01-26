class AutoLabelLogic:
    def __init__(self):
        pass

    def run(self, ok_images, ng_images):
        print("Auto labeling started")
        print("OK images:", len(ok_images))
        print("NG images:", len(ng_images))

        # TODO:
        # detect capacitor
        # check polarity
        # generate XML
        # convert TXT
