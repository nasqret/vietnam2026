
import json,os,resource,signal,subprocess,time
resource.setrlimit(resource.RLIMIT_CPU,(5,6))
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
signal.alarm(30)
assert os.getuid()==105923
commands=[['squeue','--array','-h','-u','105923','-o','%i|%T|%j|%b'],['sacct','-X','-j','21911728','--noheader','--parsable2','--format=JobID,User,Account,Partition,State,ExitCode,AllocTRES'],['sacctmgr','-nP','show','associations','where','user=plgnasqret','format=Cluster,Account,Partition'],['sinfo','-h','-o','%P|%a|%l|%D']]
for command in commands:
 began=time.monotonic()
 try:
  result=subprocess.run(command,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=5)
  assert len(result.stdout)<=65536
  record={'command':command,'actual_exit_code':result.returncode,'elapsed_seconds':time.monotonic()-began,'output':result.stdout.decode('utf-8','replace'),'read_only':True}
 except subprocess.TimeoutExpired as e:
  record={'command':command,'timeout':True,'elapsed_seconds':time.monotonic()-began,'output':(e.stdout or b'')[:65536].decode('utf-8','replace'),'read_only':True}
 print(json.dumps(record),flush=True)
print(json.dumps({'completed':True,'allocations':0,'mutating_commands':0}),flush=True)
signal.alarm(0)

