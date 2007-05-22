#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ['ThreadedClient']

import System as s
import System.Net as sn
import System.Net.Sockets as sns
import System.Net.Security
import System.Threading as st
import System.Security.Authentication
import System.Security.Cryptography.X509Certificates

import Queue
import time
import threading

##########################################################
# .NET Threaded client
##########################################################

class ThreadedClient(object):
    def __init__(self, host, port, certificate=None,
                 certificate_key=None, certificate_password_cb=None):
        self.conn = sns.TcpClient()
        self.stream = None
        self.host = host
        self.port = port
        self.lock = threading.Lock()
        self.incoming = Queue.Queue(0)
        self.incoming_cb = None
        self.th = None
        self.keep_running = True
 
    def set_parser(self, parser):
        self._parser = parser

    def get_parser(self):
        return self._parser

    def set_handler(self, handler):
        self._handler = handler

    def get_handler(self):
        return self._handler

    def start_tls(self):
        pass
        
    def connect(self):
        self.conn.Connect(self.host, self.port)
        self.stream = self.conn.GetStream()

    def disconnect(self):
        if self.connected:
            self.keep_running = False
            #self.conn.Shutdown(sns.SocketShutdown.Both)
            self.stream.Close()
            self.conn.Close()
            self.conn = None

    def connected(self):
        if self.conn:
            return self.conn.Connected
        return False
    connected = property(connected)

    def start(self):
        self.th = st.Thread(st.ThreadStart(self.run))
        self.th.Start()

    def join(self):
        if self.th and self.th.IsAlive:
            self.th.Join()
            self.th = None
        
    def propagate(self, data, size=4096):
        print "-> ", data
        bytes = System.Text.Encoding.UTF8.GetBytes(data)
        try:
            self.lock.acquire()
            self.stream.Write(bytes, 0, bytes.Length)
        finally:
            self.lock.release()
            
    def run(self):
        while self.keep_running:
            data = None
            bytes = System.Array.CreateInstance(System.Byte, self.conn.ReceiveBufferSize)
            try:
                time.sleep(0.002)
                self.lock.acquire()
                if self.stream.DataAvailable:
                    received = self.stream.Read(bytes, 0, self.conn.ReceiveBufferSize)
                    data = System.Text.Encoding.UTF8.GetString(bytes[:received])
##             if conn.Poll(-1, sns.SelectMode.SelectRead):
##                 bytes = System.Array.CreateInstance(System.Byte, 4096)
##                 received = conn.Receive(bytes)
##                 data = System.Text.Encoding.UTF8.GetString(bytes[:received])
            finally:
                self.lock.release()
            if data:
                print "<- ", data
                if self.incoming:
                    self.incoming.put(data)
                if self.incoming_cb:
                    self.incoming_cb(data)


