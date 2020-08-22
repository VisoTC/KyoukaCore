
from Core import KyoukaCore
import logging

logging.basicConfig(level=logging.INFO)
'''from Plugin.PCR.main import PCR
import logging

logging.basicConfig(level=logging.INFO)
#logging.getLogger("peewee").setLevel(logging.DEBUG)


pcr = PCR("a", 'test')
print(pcr.reportScore("10", "0", 3000000)[0])
print(pcr.reportScore("10", "0", 3000000)[0])
print()
print(pcr.currentBossInfo("10"))
print()
print(pcr.reportScore("10", "0", 6000000)[0])
b = pcr.queryDamageASMember("10", "0")
print("击杀报告")
for row in b:
    print(row)
'''

KyoukaCore().run()

