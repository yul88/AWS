# Compute
概述TBD

---
### EC2命名规则说明
m5d.xlarge

123 4，每一位的解释如下：
1. 实例家族
2. 代别：数字越大性价比越高
3. 特性:
    * a: AMD CPU，x86核心，比Intel的便宜一些
    * d: 带实例存储，和计算资源绑定，存储带宽和IOPS超高，但关机会丢实例存储上的数据。
    * g: AWS Graviton CPU, ARM核心，性价比最高，适合Web Server，Database，Spark, Java/Python程序等。
    * n: 网络优化型，用来跑高网络吞吐量的负载。
4. 大小: xlarge代表4个vCPU。

常用EC2类型 | 特点
:--- | :---
c | CPU:MEM = 1:2, 计算性能超同代m系列20%左右
m | CPU:MEM = 1:4，如果不知道选哪种就选它
r | CPU:MEM = 1:8，计算性能同m系列
t | 性能突增型，计算性能上限同m系列，网络带宽弱于m系列

---
### EC2私钥丢失

AWS不会保存私钥，需要重新创建密钥对
1. 关机(**副作用**：非EIP的公网IP会变化，实例存储InstanceStore上的数据会丢失)
2. 把EBS从EC2(A)分离Detach，然后挂载在另一台能登陆的EC2(B)上面
3. mount ebs 到路径，如/mount
4. 修改/mount/home/ec2-user/.ssh/authorized_keys，改成新密钥对中的**公钥**
5. umount /mount
6. 把EBS从EC2(B)分离，重新挂载到EC2(A)
7. EC2(A)开机，用新的密钥对中的**私钥**登陆

---
### EC2计划事件

一般是EC2底层硬件维护，在计划事件的维护窗口，EC2会重启(**reboot**)。计划事件造成的重启不会变成底层硬件，也不会造成IP变更或实例存储的内容丢失。

如果想避开计划事件，也可以主动通过关机(**stop**)再开机(**start**)的方式让EC2虚机做底层硬件的迁移。

但是有两点要注意：

1. 关机(**stop**)之后，非弹性IP(**EIP**)的公有IP地址会被收回，再开机(**start**)之后会分配到不同的公有IP。

   只有使用EIP才能保证公有IP不发生变化。另外，内网IP地址是不受关机影响的。

2. 实例存储(**Instance Store**)是绑定在底层硬件上的，无法迁移。关机后会丢失。

   3系列EC2，以及m5d等d结尾的机型会有[实例存储](https://www.cisco.com/c/en/us/products/collateral/security/firepower-2100-series/datasheet-c78-742473.html)。

   所有EC2的根分区都是EBS存储，大部分机型也只支持EBS。

   EBS是和底层硬件是分离的，不受关机的影响。

