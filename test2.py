import threading
import time
class TEST2:
    
    def __init__(self) -> None:
        self.ww=2
    def ss(self) :
        while 1:
            self.ww+=1
            time.sleep(0.2)  
           
        
    def change(self):
        command_thread : threading.Thread = threading.Thread(target=self.ss)
        command_thread.daemon=True
        command_thread.start()
        
    def tt(self):
        return self.ww