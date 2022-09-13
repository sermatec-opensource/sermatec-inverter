import os
from src.sermatec_inverter import Sermatec
import unittest
import logging

class TestSermatecBasic(unittest.IsolatedAsyncioTestCase):
    
    HOST : str = None
    PORT : int = None

    async def test_connect(self):
        smc = Sermatec(logging, self.HOST, self.PORT)
        self.assertTrue(await smc.connect())
        await smc.disconnect()
    
    def setUp(self):
        self.HOST = "PLACEHOLDER"
        self.PORT = 8899

if __name__ == "__main__":
    unittest.main()
            
        