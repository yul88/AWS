# Storage
概述TBD

---
### EBS的类型和性能
EBS | io2 | io1 | gp3 | gp2 | st1 | sc1
:--- | ---: | ---: | ---: | ---: | ---: | ---:
概述 | 高性能SSD | 高性能SSD ｜ 普通SSD | 普通SSD | 高速HDD | 普通HDD
持久性 | 99.999% | 99.8-99.9% | 99.8-99.9% | 99.8-99.9% | 99.8-99.9% | 99.8-99.9%
卷大小 | 4GiB-16TiB | 4GiB-16TiB | 1GiB-16TiB | 1GiB-16TiB | 125GiB-16TiB | 125GiB-16TiB
卷最大IOPS | 64000 | 64000 | 16000 | 16000 | 500 | 250
卷最大吞吐量MiB/s | 1000 | 1000 | 1000 | 250 | 500 | 250

性能免配置型 | gp3默认配置 | gp2 | st1 | sc1
基准性能 | 3000IOPS | 3IOPS/GiB | 40MiB/S /TiB | 12MiB/S /TiB
突增性能 | - | 3000IOPS | 250MiB/S /TiB | 80MiB/S /TiB
比较小的盘可能无法达到突增性能的上限，突增能维持的时间也和大小相关，[参考页面](https://docs.aws.amazon.com/zh_cn/AWSEC2/latest/UserGuide/ebs-volume-types.html)

新推出的GP3类型SSD EBS，可以用默认配置，也可以预配置性能。相比GP2类型相同的性能下价格更低。
预配置性能型 | io2 | io1 | gp3
性能配比上限 | 500IOPS/GiB | 50IOPS/GiB | 500IOPS/GiB


---
### EC2和EBS之间的带宽
每类EC2都有不同的EBS带宽，[参考](https://docs.aws.amazon.com/zh_cn/AWSEC2/latest/UserGuide/ebs-optimized.html)。

常见机型的EBS**基准**带宽如下：
IOPS(16KiB IO) | large | xlarge | 2xlarge
:--- | ---: | ---: | ---:
t3/t3a | 4000 | 4000 | 4000
c5 | 4000 | 6000 | 10000
m5/r5 | 3600 | 6000 | 12000
m5a/r5a | 3600 | 6000 | 8333
c6g/m6g/r6g | 3600 | 6000 | 12000

吞吐量MB/s(128KiB IO) | large | xlarge | 2xlarge
:--- | ---: | ---: | ---:
t3/t3a | 86.86 | 86.86 | 86.86
c5/m5/r5| 81.25 | 143.75 | 287.50
m5a/r5a | 81.25 | 135.63 | 197.50
c6g/m6g/r6g | 78.75 | 148.50 | 296.87

AWS保证每24小时至少有30分钟可以达到**突发**带宽。常见机型的EBS**突发**带宽如下：
IOPS(16KiB IO) | large | xlarge | 2xlarge
:--- | ---: | ---: | ---:
t3/t3a | 15700 | 15700 | 15700
c5 | 20000 | 20000 | 20000
m5/r5 | 18750 | 18750 | 18750
m5a/r5a | 16000 | 16000 | 16000
c6g/m6g/r6g | 20000 | 20000 | 20000

吞吐量MB/s(128KiB IO) | large | xlarge | 2xlarge
:--- | ---: | ---: | ---:
t3/t3a | 347.50 | 347.50 | 347.50
c5/m5/r5| 593.75 | 593.75 | 593.75
m5a/r5a | 360.00 | 360.00 | 360.00
c6g/m6g/r6g | 593.75 | 593.75 | 593.75

EC2和EBS之间的带宽与EBS的带宽共同限制了EBS能达到的性能。

例如，EBS卷达到了16000 IOPS，但是如果机型是m5.2xlarge，那么最终只能达到12000IOPS。

---
### EBS扩盘

每6小时可以在线扩展一次EBS盘的大小。只能扩展，无法收缩。

* 扩展EBS大小
EC2 > 卷 > 选中要修改的卷 > 操作 > 修改卷 > 增加卷的大小

    注意：
    * 修改卷以后，冷却时间6小时后才能再次修改
    * 文件块默认4096字节的情况下，MBR分区最大支持2TiB，GPT分区最大支持16TiB
    * EBS类型也可以在线修改，但是根分区只支持gp2/gp3类型
    * 卷修改后容量能马上变化，但是性能达到新容量的标准需要执行一段时间

* 扩展文件系统，[参考](https://docs.aws.amazon.com/zh_cn/AWSEC2/latest/UserGuide/recognize-expanded-volume-linux.html)。

下面是扩展根分区的例子：

注意：如果对修改文件分区命令不熟悉，建议做好**快照**再操作。
```bash
# 查看文件系统和分区
df -hT
lsblk

# NVME EBS
sudo growpart /dev/nvme0n1 1
# EBS
sudo growpart /dev/xvda 1

# NVME EBS: EXT4卷
sudo resize2fs /dev/nvme1n1
# EBS：EXT4卷
sudo resize2fs /dev/xvda1

# NVME EBS或EBS：XFS卷
sudo yum install xfsprogs
sudo xfs_growfs -d /
```

