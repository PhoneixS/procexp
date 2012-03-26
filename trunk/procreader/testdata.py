cpuInfo = """
processor  : 0
vendor_id  : GenuineIntel
cpu family  : 6
model    : 42
model name  : Intel(R) Core(TM) i7-2720QM CPU @ 2.20GHz
stepping  : 7
cpu MHz    : 2195.089
cache size  : 6144 KB
fdiv_bug  : no
hlt_bug    : no
f00f_bug  : no
coma_bug  : no
fpu    : yes
fpu_exception  : yes
cpuid level  : 13
wp    : yes
flags    : fpu vme de pse tsc msr pae mce cx8 apic mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss nx rdtscp lm constant_tsc up arch_perfmon pebs bts xtopology tsc_reliable nonstop_tsc aperfmperf pni pclmulqdq ssse3 cx16 sse4_1 sse4_2 popcnt aes xsave avx hypervisor lahf_lm ida arat epb xsaveopt pln pts dts
bogomips  : 4390.17
clflush size  : 64
cache_alignment  : 64
address sizes  : 40 bits physical, 48 bits virtual
power management:
"""

procNetTcp = """
  sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode                                                     
   0: 00000000:0016 00000000:0000 0A 00000000:00000000 00:00000000 00000000     0        0 7543 1 00000000 300 0 0 2 -1                              
   1: 0100007F:0277 00000000:0000 0A 00000000:00000000 00:00000000 00000000     0        0 16428 1 00000000 300 0 0 2 -1                             
   2: 0100007F:8D7A 0100007F:9357 01 00000000:00000000 00:00000000 00000000  1000        0 15314 1 00000000 20 4 28 10 -1                            
   3: 0100007F:E984 0100007F:A4FD 01 00000000:00000000 00:00000000 00000000  1000        0 15319 1 00000000 20 0 0 10 -1                             
"""

procNetDev = """
Inter-|   Receive                                                |  Transmit
 face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed
    lo:  998538     730    0    0    0     0          0         0   998538     730    0    0    0     0       0          0
  eth0: 13338908   12362    0    0    0     0          0         0   926392    8280    0    0    0     0       0          0
"""