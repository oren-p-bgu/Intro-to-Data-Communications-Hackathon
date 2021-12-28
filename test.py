import multiprocessing
import threading
import time
import getch

class myThread (multiprocessing.Process):
    def __init__(self, threadID, name, cont):
        super(myThread, self).__init__()
        #threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.cont = cont
        
    def run(self):
        print ("Starting " + self.name +"\n")
        char = getch.getch()
        print ('You pressed %s' % char)
        cont.append(1)
        print ("Terminating" + self.name)

cont = []

thread1 = myThread(1, "Thread1", cont)

thread1.start()

while cont == []: 
    print ("Running")
    time.sleep(0.5)