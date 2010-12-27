import threading 
class AsyncMethod(object):
  '''The asynchronous method object associated with an instance.'''
  def __init__(self, descriptor, instance, altReturn):
    self.__descriptor = descriptor
    self.__name__ = descriptor.__name__
    self.__instance = instance
    self.__running = []
    self.__return = altReturn

  def join_all(self):
    '''Joins all threads'''
    for thread in self.running:
      thread.join()
  
  @property
  def running(self):
    '''Return the threads started by this object's __call__ method that are 
    still alive.'''
    self.__running = [t for t in self.__running if t.isAlive()]
    return self.__running
  
  def __call__(self, *args, **kwargs):
    t = self.__descriptor.call(self.__instance, *args, **kwargs)
    self.__running.append(t)
    if not (self.__return is AsyncMethodDescriptor.THREAD):
      return self.__return
    return t
    

class AsyncMethodDescriptor(object):
  '''This class encapsulates an asynchronous method. It is the replacement for
  the original method. '''
  
  class _threadsingleton(object):
    '''Just to get the documentation nice :)'''
    def __repr__(self):
      return 'THREAD'
    
  #: If the requested return value of an asynchronous method is this object, 
  #: the newly created thread is returned 
  THREAD = _threadsingleton()
  
  def __init__(self, method, errorHandler=None, altReturn=THREAD, daemon=False):
    '''This is an :func:`@asynchronous <utils.asynchronous>` method. '''
    self.__method = method
    self.__name__ = method.__name__
    self.__return = altReturn
    self.__daemon = daemon
    self.onError = errorHandler
    self.__doc__ = self.__init__.__doc__
    if method.__doc__:
      self.__doc__ += method.__doc__
  
  def __get__(self, instance, _):
    if instance is None:
      return self
    try:
      return instance.__dict__[self.__name__]
    except:
      m = AsyncMethod(self, instance, self.__return)
      instance.__dict__[self.__name__] = m
      return m
  
  def __run(self, obj, *args, **kwargs):
    '''This is the target of the thread that is launched upon execution of an
    AsyncMethod object.''' 
    try:
      threadtype = 'Daemon thread' if threading.currentThread().daemon else 'Thread'
      if obj is not None:
        self.__method(obj, *args, **kwargs)
      else:
        self.__method(*args, **kwargs)
    except:
      if callable(self.onError):
        try:
          self.onError(obj, self.__method)
        except:
          pass
      else:
        pass
  
  def call(self, obj, *args, **kwargs):
    '''
    This method is called by :class:`AsyncMethod <utils.AsyncMethod>` to 
    create a new thread. The `obj` parameter is the instance on which the 
    asynchronous method was called and should therefore be treated as the *self*
    parameter of the target method.
    '''
    t = threading.Thread(target=self.__run, args=(obj,) + args, 
                         name=self.__method.__name__, kwargs=kwargs)
    t.daemon = self.__daemon
    t.start()
    return t
  
  def __call__(self, *args, **kwargs):
    '''This method is called when the decorator is used on a function in the 
    global namespace (rather than a method).'''
    t = threading.Thread(target=self.__run, args=(None,) + args, 
                         name=self.__method.__name__, kwargs=kwargs)
    t.setDaemon(self.__daemon)
    t.start()
    return t if self.__return == AsyncMethodDescriptor.THREAD else self.__return
    

def asynchronous(errorHandler, altReturn=AsyncMethodDescriptor.THREAD, 
                 daemon=False):
  '''
  Asynchronous execution decorator. The code below demonstrates its use. This
  decorator takes a single mandatory parameter, `errorHandler`. If this 
  parameter is :const:`None`, any exceptions thrown in the spawned thread are 
  logged. If it is set to a callable object, `errorHandler` is called 
  from the exception context, with the originating method as a paramter.
  
  If *altReturn* is specified, that value will be returned from a call to the
  asynchronous method, rather than the newly created thread.
  
  If *daemon* is set, the new thread will be started as a daemon thread.
  
  Below is some example code that demonstrates the use of this decorator.
  ::
  
      from utils import asynchronous
      import time
       
      class C(object):
        def __onerror(self, method):
          print 'Exception in %s' % method.__name__
          
        def doSomething(self, fail):
          if fail:
            raise Exception() # Caught in __onerror
          else:
            for i in range(1, 5):
              time.sleep(1) 
       
        @asynchronous(__onerror)
        def run1(self, fail):
          self.doSomething(fail)
           
        @asynchronous(None, None)
        def run2(self, fail):
          self.doSomething(fail)
              
      c = C()
      print c.run1(False) # Returns the newly created thread
      print c.run2(False) # Returns the newly created thread
      c.run1(True)  # Exception caught in c.__onerror
      c.run2(True)  # Exception caught by AsyncMethod
      # c.run1 is an AsyncMethod object
      # C.run1 is an AsyncMethodDescriptor object
      for t in c.run1.running:
        t.join()
      # Above is equivalent to;
      c.run2.join_all()
  '''
  return lambda x: AsyncMethodDescriptor(x, errorHandler=errorHandler,
                                         daemon=daemon, altReturn=altReturn)
