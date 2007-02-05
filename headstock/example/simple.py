from headstock.handler.client import AsyncClient

if __name__ == '__main__':
    from bridge.parser.bridge_expat import Parser
    from bridge import Element as E
    E.parser = Parser
    from bridge.parser.incremental import create_parser

    def user_online(p, e):
        print unicode(e.get_attribute('from'))
    
    def user_unavailable(p, e):
        print unicode(e.get_attribute('from'))

    def user_subscription_requested(p, e):
        jid = unicode(e.get_attribute('from'))
        p.allow_subscription(jid)
    
    from headstock.core.stream import Stream
    
    c = AsyncClient('localhost', 5222)
    parser, handler, output = create_parser()
    c.set_parser(parser)
    c.set_handler(handler)
    c.connect()

    s = Stream(u'localhost', c)
    s.set_auth('test', 'test')
    s.set_resource_name(u'headstock')
    s.initialize_all()
    
    p = s.presence
    p.register_online(user_online)
    p.register_unavailable(user_unavailable)
    p.register_subscribe(user_subscription_requested)

    s.initiate()

    import asyncore
    asyncore.loop()
    
    
##     import threading
##     th = threading.Thread(target=c.loop)
        
##     th.start()
##     s.initiate()

##     import time

##     while 1:
##         try:
##             time.sleep(1)
##         except KeyboardInterrupt:
##             c.run = False
##             th.join()
##             c.disconnect()
##             break
