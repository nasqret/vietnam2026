
import json,os,pwd,signal,subprocess,time
signal.alarm(30)
assert os.getuid()==105923, "Unexpected remote owner"
user=pwd.getpwuid(os.getuid()).pw_name
assert user=="plgnasqret", "Unexpected remote user"
commands=[
 ["sacctmgr","-n","-P","show","associations","where","user="+user,
  "format=Cluster,Account%80,User%40,Partition%40,QOS%120,DefaultQOS%80"],
 ["sinfo","--noheader","--format=%P|%a|%l|%G|%D|%c|%m"],
 ["scontrol","-o","show","partition","plgrid"],
]
rows=[]
started=time.monotonic()
for command in commands:
 try:
  process=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=8)
  assert len(process.stdout.encode())<=65536 and len(process.stderr.encode())<=8192,"Metadata output bound exceeded"
  rows.append({"argv":command,"exit_code":process.returncode,"stdout":process.stdout,"stderr":process.stderr})
 except Exception as error:
  rows.append({"argv":command,"exit_code":None,"error":type(error).__name__+": "+str(error)[:500]})
print(json.dumps({"schema":"hydra-owned-cpu-metadata-v1","uid":os.getuid(),"user":user,"commands":rows,
 "elapsed_seconds":time.monotonic()-started,"scheduler_mutations":0,"uploads":0,"native_runs":0,"model_calls":0,"gpu_allocations":0,"automatic_retry":False}),flush=True)
