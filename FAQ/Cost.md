# Cost
概述TBD

---
### 监控Metric指标

---
### 选择合适的价格模型
价格模型 | 特点
:-- | :--
按需实例(On Demand) | 按秒计费，无折扣
预留实例(Reserved) | OD的6-7折，连续包1年或3年
竞价实例(On Spot) | OD的1-2折，计算资源可能被回收

免费Linux的EC2的预留实例大部分都支持[实例大小灵活匹配](https://docs.aws.amazon.com/whitepapers/latest/cost-optimization-reservation-models/maximizing-utilization-with-size-flexibility-in-regional-reserved-instances.html)，比如:

* 比如1个m5.xlarge的RI可以匹配2个m5.large的EC2
* 比如4个c5.large的RI可以匹配1个c5.2xlarge的EC2

注意：
* Windows实例，Redhat/SUSE Linux实例，G4实例，专用主机，指定可用区的RI，它们不支持灵活匹配。
* ElasticSearch，ElastiCache, RDS SQL Server不支持灵活匹配。

---
### 选择合适的EC2类型

#### m5d.xlarge
#### 123 4
解释见下面

EC2类型命名规则:
1. 实例家族
2. 代别：数字越大性价比越高
3. 特性:
    * a: AMD CPU，x86核心，比Intel的便宜一些
    * d: 带实例存储，和计算资源绑定，存储带宽和IOPS超高，但关机会丢实例存储上的数据。
    * g: AWS Graviton CPU, ARM核心，性价比最高，适合Web Server，Database，Spark, Java/Python程序等。
    * n: 网络优化型，用来跑高网络吞吐量的负载。
4. 大小: xlarge代表4个vcore。

常用EC2类型 | 特点
:--- | :---
c | CPU:MEM = 1:2, 计算性能超同代m系列20%左右
m | CPU:MEM = 1:4，如果不知道选那种就选它
r | CPU:MEM = 1:8，计算性能同m系列
t | 性能突增型，计算性能上限同m系列，网络带宽弱于m系列

选t类型用于开发测试和偶尔出现Load波峰的生产负载可以极大降低成本。
t系列能一直满足[基准性能](https://docs.aws.amazon.com/zh_cn/AWSEC2/latest/UserGuide/burstable-credits-baseline-concepts.html)，以t3/t3a类型为例：
实例大小 | 空闲1小时获得CPU积分 | 可累积的最大积分 | vcore | 每个vCPU的基准利用率 | mem
:--- | ---: | ---: | ---: | ---: | ---:
nano | 6 | 144 | 2 | 5% | 0.5
micro | 12 | 288 |2 | 10% | 1.0
small | 24 | 576 | 2 | 20% | 2.0
medium | 24 | 576 | 2 | 20% | 4.0
large | 36 | 864| 2 | 30% | 8.0
xlarge | 96 | 2304 | 4 | 40% | 16.0
2xlarge | 192 | 4608 | 8 | 40% | 32.0

t系列机型的积分规则(计算精确到毫秒)：
* 如果CPU利用率小于基准性能，累计积分
* 如果CPU利用率大于基准性能，消耗积分
* 积分耗尽，并且透支了可累计最大积分以后
    * 如果是普通模式，性能被限制到基准性能
    * 如果是无限模式，性能不受限制，但会[额外收费](https://www.amazonaws.cn/ec2/pricing/)

以t3.large为例，假设它没有累计积分，此时它能通过透支积分的方式达到m5.large的100%的计算性能
* 如果负载把2个vcore跑满，每小时净消耗(100%*2*60-36)=84分，透支积分能连续跑10.28小时。
* 如果负载把1个vcore跑满，另一个空闲，每小时净消耗(100%*60-36)=24分，透支积分能连续跑36小时。
* 如果负载把1个vcore跑到60%，另一个空闲，不消耗积分也不累计积分(60%*60-36=0)。

为节省成本，选t3a还是选m5a，存在性价比的问题。

以2021年2月时点的价格计算，无限模式下，每vCPU小时收费¥0.342。

1年无预付Linux RI每小时价格:
实例类型 | 宁夏区RI ｜ 北京区RI
:--- | ---: | ---:
t3a.large | 0.1109 | 0.1664
m5a.large | 0.1890 | 0.3180
t3a.xlarge | 0.2219 | 0.3328
m5a.xlarge | 0.3780 | 0.6360
t3a.2xlarge | 0.4437 | 0.6657
m5a.2xlarge | 0.7570 | 1.2710

t3a相对于m5a每小时节省的成本：
实例大小 | 宁夏区差额 ｜ 宁夏区vCPU小时数 | 北京区差额 | 北京区vCPU小时数
:--- | ---: | ---: | ---: | ---:
large | 0.0781 | 0.228 | 0.1516 | 0.443
xlarge | 0.1561 |0.456 | 0.3032 | 0.886
2xlarge | 0.3133 | 0.916 | 0.6053 | 1.769

t3a相比m5a的盈亏利用率:
实例大小 | 基准性能 ｜ 宁夏区 | 北京区
:--- | ---: | ---: | ---:
large | 30% | 41.4% | 52.1%
xlarge | 40% | 51.4% | 62.1%
2xlarge | 40% | 51.4% | 62.1%

---
### 利用弹性伸缩

---
### 选择合适类型的存储和数据库

___
### 合理规划网络

